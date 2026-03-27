from dataclasses import dataclass, field
from typing import Optional, Self, Protocol, Any, Never, TypeVar, overload, runtime_checkable
"""
Functional error handling system with:
- Result composition
- Error accumulation
- Type-safe operations

Core concepts:
- Result: Operation outcome (success/failure)
- ErrorPropagator: Error accumulation mechanism
- Collector: Value container with error handling
"""


class Result(Protocol):
    value: Any
    err: Optional[ExceptionGroup]

    """Protocol for operation results"""
    def is_ok(self) -> bool:
        """Returns True if successful (no errors)"""

    def unwrap(self) -> Any:
        """Returns value or raises exception if errors exist"""

    def has(self, target_value: Any, exception_type: Optional[type[Exception]] = None) -> bool:
        """"""


class Ok(Result):
    """Singleton success marker without value"""
    def is_ok(self) -> bool:
        return True

    def __str__(self) -> str:
        return "OK"

    @property
    def value(self) -> "Ok":
        return OK

    def unwrap(self) -> "Ok":
        """Always return OK"""
        return OK

    @property
    def err(self) -> None:  # type: ignore[override]
        return None

    def has(self, target_value: Any, exception_type: Optional[type[Exception]] = None) -> bool:
        target_value
        exception_type
        return False


OK = Ok()


class Null:
    """Non value result marker"""
    def __str__(self) -> str:
        return "NULL"


NULL = Null()


class ErrorPropagator(Result, Protocol):
    """Protocol for error-accumulating types"""
    err: Optional[ExceptionGroup]

    def is_ok(self) -> bool:
        return self.err is None

    def append_e(self, e: Exception, msg: str = "") -> Self:
        """adds to existing group or creates new one"""
        if self.err is None:
            self.err = ExceptionGroup(msg, (e,))
        elif msg == self.err.message:
            self.err = ExceptionGroup(msg, (*self.err.exceptions, e))
        else:
            self.err = ExceptionGroup(msg, (e, self.err))
        return self

    def append_err(self, err: ExceptionGroup) -> Self:
        """Adds an exception or exception group to the collector.
        Rules:
        - For ExceptionGroup with matching message: merges exceptions
        - For ExceptionGroup with different message: preserves structure
        """
        if self.err is None:
            self.err = err
        elif self.err.message == err.message:
            self.err = ExceptionGroup(err.message, (*self.err.exceptions, *err.exceptions))
        else:
            self.err = ExceptionGroup(err.message, (*self.err.exceptions, err))
        return self

    def propagate_err[T](self, res: "Collector[T] | ErrorAccumulator | Ok") -> T | Null | Ok:
        """Merges errors from another result and returns its value:
        1. If res has errors - merges them into current
        2. Returns res's value (if exists)
        """
        if res.err is not None:
            self.append_err(res.err)
        return res.value if hasattr(res, "value") else NULL

    def merge_err[T: "Result"](self, res: T) -> T:
        """Merges errors from another result and returns the result itself.

        Unlike propagate_err which returns the value, merge_err returns
        the original result instance preserving its type and identity.

        Useful for chaining operations while collecting errors from intermediate results.

        Example:
            >>> collector = Simple("base")
            >>> validation_result = validate_data(data)
            >>> # Merge errors but keep validation_result for further processing
            >>> next_step = collector.merge_err(validation_result).check_something()
        """
        if res.err is not None:
            self.append_err(res.err)
        return res

    def has(self, target_value: Any, exception_type: Optional[type[Exception]] = None) -> bool:
        if self.err is None:
            return False
        return is_target(self.err, target_value, exception_type)


@dataclass(slots=True)
class Error(ErrorPropagator):
    """Error-only result container"""
    err: ExceptionGroup

    @classmethod
    def from_e(cls, e: Exception, msg: str = "") -> "Error":
        return cls(ExceptionGroup(msg, (e,)))

    def with_msg(self, msg: str) -> "Error":
        """Returns a new Error instance with updated message context
        while preserving the original exception structure
        """
        return Error(err=ExceptionGroup(msg, (self.err,)))

    def unwrap(self) -> Never:
        """Always raises exception"""
        raise self.err

    @property
    def value(self) -> Null:
        return NULL

    def has(self, target_value: Any, exception_type: Optional[type[Exception]] = None) -> bool:
        return is_target(self.err, target_value, exception_type)


@dataclass(slots=True)
class StrictOk(ErrorPropagator):
    """
    Represents a strictly successful operation that must have no errors.

    Unlike the simple Ok singleton, StrictOk can accumulate errors but will
    only be considered truly successful if no errors were accumulated.

    Use this when you need to distinguish between:
    - Pure success (Ok): no errors possible
    - Validated success (StrictOk): success only if no errors detected

    Examples:
        Data validation, sanitization, or any operation where errors
        should be tracked but don't necessarily constitute failure.
    """
    err: Optional[ExceptionGroup] = field(init=False, default=None)

    def unwrap(self) -> Ok:
        if self.err is None:
            return OK
        raise self.err

    def is_ok(self) -> bool:
        return True

    @property
    def value(self) -> Ok:
        return OK

    def as_error(self, e: Optional[Exception] = None, msg: str = "") -> Error:
        """
        Convert accumulated errors to Error instance, optionally adding a final error.

        Args:
            e: Optional final exception to add before conversion
            msg: Message for the exception group (if adding new error)

        Returns:
            Error: Contains ExceptionGroup with all accumulated errors.

        Raises:
            RuntimeError: If no errors were accumulated and no final error provided

        Useful for adding a contextual error before final conversion.
        """
        if e is not None:
            self.append_e(e, msg)
        if self.err is None:
            raise RuntimeError("Cannot convert to Error: no errors were accumulated")
        return Error(self.err)


type ValueOrError[T: Any] = T | Error


# todo: maybe will replaced by StrictOK
@dataclass(slots=True)
class ErrorAccumulator(ErrorPropagator):
    """Base container for error propagation with status conversion"""
    err: Optional[ExceptionGroup] = field(init=False, default=None)

    @property
    def result(self) -> ValueOrError[Ok]:
        """
        Finalize error accumulation and return simple Result.
        Converts this accumulator to either:
        - Ok: if no errors occurred
        - Error: with accumulated ExceptionGroup otherwise
        After conversion, this accumulator should not be used further.
        """
        if self.err is None:
            return OK
        return Error(self.err)

    def as_error(self, e: Optional[Exception] = None, msg: str = "") -> Error:
        """
        Convert accumulated errors to Error instance, optionally adding a final error.

        Args:
            e: Optional final exception to add before conversion
            msg: Message for the exception group (if adding new error)

        Returns:
            Error: Contains ExceptionGroup with all accumulated errors.

        Raises:
            RuntimeError: If no errors were accumulated and no final error provided

        Useful for adding a contextual error before final conversion.
        """
        if e is not None:
            self.append_e(e, msg)
        if self.err is None:
            raise RuntimeError("Cannot convert to Error: no errors were accumulated")
        return Error(self.err)

    def unwrap(self) -> Never:
        """ErrorAccumulator is not meant to be unwrapped directly"""
        raise RuntimeError("ErrorAccumulator should be converted to Result first")


@runtime_checkable
class Collector[T](ErrorPropagator, Protocol):
    """Protocol for value containers with error handling"""
    value: T

    def unpack(self) -> tuple[T, Optional[ExceptionGroup]]:
        return self.value, self.err

    def unwrap(self) -> T:
        """Returns value or raises exception if errors exist"""
        if self.err:
            raise self.err
        return self.value

    @property
    def result(self) -> Self | Error:
        """Finalize Collection to Self or Error"""
        if self.err is None:
            return self
        return Error(self.err)


@dataclass(slots=True)
class Simple[T](Collector[T], Result):
    """Basic collector for values"""
    value: T
    err: Optional[ExceptionGroup] = field(init=False, default=None)

    def set(self, res: "Simple[T]") -> T:
        """set value and append errors"""
        self.value = res.value
        if res.err is not None:
            self.append_err(res.err)
        return res.value


@dataclass(slots=True)
class Bool(Simple[bool], Result):
    """Specialized collector for boolean results"""
    value: bool = field(default=False)
    err: Optional[ExceptionGroup] = field(init=False, default=None)


@dataclass(slots=True)
class Option[T](Simple[Optional[T]], Result):
    """Basic collector for optional values"""
    value: Optional[T] = field(default=None)


@dataclass(slots=True)
class List[T](Collector[list[Optional[T | Ok | Null]]], Result):
    """List collector with error accumulation"""
    value: list[Optional[T] | Ok | Null] = field(init=False, default_factory=list)
    err: Optional[ExceptionGroup] = field(init=False, default=None)

    def append(self, res: Option[T] | Simple[T] | Error | Ok) -> None:
        """Appends result with rules:
        - For OK: adds OK marker
        - For Error: adds None and merges errors
        - For Collector: adds value and merges errors
        """
        if res.err is not None:
            self.append_err(res.err)
        self.value.append(res.value)

    def __add__(self, other: Option[T] | Simple[T] | Error | Ok) -> Self:
        self.append(other)
        return self


type SimpleOrError[T: Any] = Simple[T] | Error

T1 = TypeVar("T1")


class Sequence[*Ts](Collector[tuple[*Ts]], Result):
    """
    A strictly-typed heterogeneous sequence container with error handling capabilities.
    Sequence preserves the exact type and order of elements at the type level using
    variadic generics, while providing error accumulation functionality inherited
    from the error handling system.
    Key features:
    - Type-safe heterogeneous collections: Sequence[int, str, bool] for (1, "hello", True)
    - Error propagation: Accumulates and manages exceptions through ExceptionGroup
    - Protocol compliance: Implements Collector and Result protocols for interoperability
    Examples:
        >>> seq = Sequence(1, "hello", True)  # Inferred as Sequence[int, str, bool]
        >>> seq.value  # (1, "hello", True)
        >>> seq.unwrap()  # Type-safe tuple unpacking

        >>> error_seq = Sequence(1, "test", err=ExceptionGroup("error", [ValueError()]))
        >>> seq.is_ok()  # False
    """
    value: tuple[*Ts]
    err: Optional[ExceptionGroup]

    def __init__(self, *values: *Ts, err: Optional[ExceptionGroup] = None) -> None:
        self.value = values
        self.err = err

    @overload
    def add(self, res: Collector[T1]) -> "Sequence[*Ts, T1]": ...

    @overload
    def add(self, res: Error) -> "Sequence[*Ts, Null]": ...

    @overload
    def add(self, res: Ok) -> "Sequence[*Ts, Ok]": ...

    def add(self, res: Collector[T1] | Error | Ok) -> "Sequence[*Ts, Any]":
        """Basic adding method"""
        new_value = self.value + (res.value,)
        new = Sequence(*new_value, err=self.err)
        if res.err is not None:
            new.append_err(res.err)
        return new

    def __str__(self) -> str:
        return f"({", ".join(map(str, self.value))}){"" if not self.err else str(self.err)}"


def is_target(exc_group: ExceptionGroup, target_value: Any, exception_type: Optional[type[Exception]] = None) -> bool:
    """
    has target Exception with value in group
    """
    stack = [exc_group]
    while stack:
        current = stack.pop()
        for exc in current.exceptions:
            if isinstance(exc, ExceptionGroup):
                stack.append(exc)
            elif (
                (
                    exception_type is None
                    or isinstance(exc, exception_type)
                )
                and exc.args
                and exc.args[0] == target_value
            ):
                return True
    return False


def check[T: Any](value: ValueOrError[T]) -> T:
    if isinstance(value, Error):
        raise value.err
    return value


__all__ = [
    "SimpleOrError",
    "ValueOrError"
]
