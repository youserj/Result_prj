from dataclasses import dataclass, field
from typing import Optional, Self, Protocol, Iterator, Any


class Result(Protocol):
    msg: str

    def is_ok(self) -> bool: ...


class ErrorPropagator(Result, Protocol):
    err: Optional[ExceptionGroup]

    def is_ok(self) -> bool:
        return self.err is None

    def append_err(self, e: Exception | ExceptionGroup) -> Self:
        """append except"""
        if isinstance(e, ExceptionGroup):
            if self.err is None:
                self.err = e
            elif self.msg == e.message:
                self.err = ExceptionGroup(self.msg, (*self.err.exceptions, *e.exceptions))
            else:
                self.err = ExceptionGroup(self.msg, (*self.err.exceptions, e))
        else:  # for Exception
            if self.err is None:
                self.err = ExceptionGroup(self.msg, (e,))
            elif self.msg == self.err.message:
                self.err = ExceptionGroup(self.msg, (*self.err.exceptions, e))
            else:
                self.err = ExceptionGroup(self.msg, (e, self.err))
        return self

    def propagate_err[T](self, res: "Collector[T]") -> Optional[T]:
        """Propagates (merges) the error from another Result into this one, returning its value"""
        if res.err is not None:
            self.append_err(res.err)
        return res.value if hasattr(res, "value") else None


class Collector[T](ErrorPropagator, Protocol):
    value: T

    def __iter__(self) -> Iterator[Any]:
        return iter((self.value, self.err))

    def unwrap(self) -> T:
        if self.err:
            raise self.err
        return self.value


@dataclass(slots=True)
class Simple[T](Collector[Optional[T]], Result):
    msg: str = ""
    value: Optional[T] = field(default=None)
    err: Optional[ExceptionGroup] = field(init=False, default=None)

    def set(self, res: "Simple[T]") -> Optional[T]:
        """set value and append errors"""
        self.value = res.value
        return self.propagate_err(res)


@dataclass(slots=True)
class Null(Result):
    msg: str = ""

    def is_ok(self) -> bool:
        return False


@dataclass(slots=True)
class OK(Result):
    msg: str = ""

    def is_ok(self) -> bool:
        return True


class Error(ErrorPropagator):
    __slots__ = ("msg", "err")
    err: ExceptionGroup

    def __init__(self, e: Exception, msg: str = "") -> None:
        self.msg = msg
        self.err = ExceptionGroup(self.msg, (e,))


@dataclass(slots=True)
class List[T](Collector[list[Optional[T]]], Result):
    msg: str = ""
    value: list[Optional[T]] = field(init=False, default_factory=list)
    err: Optional[ExceptionGroup] = field(init=False, default=None)

    def append(self, res: Collector[Optional[T]] | Error | OK | Null) -> None:
        """append value and errors if possible"""
        if hasattr(res, "value"):
            self.value.append(res.value)
        if (
            hasattr(res, "err")
            and res.err is not None
        ):
            self.append_err(res.err)

    def __add__(self, other: Collector[Optional[T]] | Error | OK | Null) -> Self:
        self.append(other)
        return self
