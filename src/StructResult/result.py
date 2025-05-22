from dataclasses import dataclass, field
from typing import Optional, Self, Any, Protocol, Iterator, Final


class Result[T](Protocol):
    value: Optional[T]
    err: Optional[ExceptionGroup]
    msg: str = ""

    def __iter__(self) -> Iterator[T | ExceptionGroup[Exception] | None]:
        return iter((self.value, self.err))

    def unwrap(self) -> Optional[T]:
        if self.err:
            raise self.err
        return self.value

    def is_ok(self) -> bool:
        return self.err is None


class ErrorGrouper(Protocol):
    err: Optional[ExceptionGroup]
    msg: str = ""

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


class ErrorPropagator(ErrorGrouper, Protocol):
    def propagate_err[T](self, res: Result[T]) -> Optional[T]:
        """Propagates (merges) the error from another Result into this one, returning its value"""
        if res.err is not None:
            self.append_err(res.err)
        return res.value


class Appender[T](ErrorPropagator, Protocol):
    def append(self, res: Result[T]) -> Optional[T]: ...


@dataclass(slots=True)
class Simple[T](Result[T], Appender[T]):
    value: Optional[T] = field(default=None)
    msg: str = field(default="")
    err: Optional[ExceptionGroup] = field(init=False, default=None)

    def append(self, res: Result[T]) -> Optional[T]:
        """set value and append errors"""
        self.value = res.value
        return self.propagate_err(res)


@dataclass(frozen=True)
class Null(Result[Any]):
    value: Final[None] = None
    err: None = None


NONE = Null()
"""None result"""


@dataclass(slots=True)
class Error(ErrorPropagator, Result[Any]):
    value: Final[None] = field(default=None)
    msg: str = field(default="")
    err: Optional[ExceptionGroup] = field(init=False, default=None)


@dataclass(slots=True)
class List[T](Appender[T], Result[list[Optional[T]]]):
    msg: str = field(default="")
    value: Optional[list[Optional[T]]] = field(init=False, default=None)
    err: Optional[ExceptionGroup] = field(init=False, default=None)

    def append(self, res: Result[T]) -> Optional[T]:
        """append value and errors"""
        if self.value is None:
            self.value = []
        self.value.append(res.value)
        return self.propagate_err(res)

    def __add__(self, other: Result[T]) -> Self:
        self.append(other)
        return self
