from typing import Optional, TypeVar, Generic, Self, Any
from abc import ABC, abstractmethod

T = TypeVar("T")

empty = tuple()


class Result(Generic[T], ABC):
    value: Optional[T]
    err: Optional[ExceptionGroup]
    msg: str = ""
    __slots__ = empty

    def __getitem__(self, item):
        if item == 0:
            return self.value
        elif item == 1:
            return self.err
        else:
            raise StopIteration

    @abstractmethod
    def append(self, res: Self) -> T:
        """"""

    def append_err(self, e: Exception | ExceptionGroup):
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

    def unwrap(self) -> T:
        if self.err:
            raise self.err
        return self.value

    def is_ok(self) -> bool:
        return self.err is None


class Simple(Result, Generic[T]):
    __slots__ = ("value", "err", "msg")

    def __init__(self, value: Optional[T] = None, e: Exception = None, msg: str = ""):
        self.value = value
        if e is not None:
            self.err = ExceptionGroup(msg, (e,))
        else:
            self.err = None
        self.msg = msg

    def append(self, res: Result) -> T:
        """set value and append errors"""
        self.value = res.value
        if res.err is not None:
            self.append_err(res.err)
        return res.value


class Null(Result):
    """can't append value or errors"""
    __slots__ = empty

    def append(self, res: Self):
        raise RuntimeError(F"can't append for {self.__class__.__name__}")

    @property
    def value(self):
        return None

    @property
    def err(self):
        return None


NONE = Null()
"""None result"""


class Error(Result):
    __slots__ = ("err", "msg")

    def __init__(self, e: Exception = None, msg: str = ""):
        if e is not None:
            self.err = ExceptionGroup(msg, (e,))
        else:
            self.err = None
        self.msg = msg

    def append(self, res: Result) -> Any:
        if res.err is not None:
            self.append_err(res.err)
        return res.value

    @property
    def value(self):
        return None


class List(Result, Generic[T]):
    value: list[T]
    __slots__ = ("value", "err", "msg")

    def __init__(self, msg: str = ""):
        self.value = list()
        self.err = None
        self.msg = msg

    def append(self, res: Result[T]) -> T:
        """append value and errors"""
        self.value.append(res.value)
        if res.err is not None:
            self.append_err(res.err)
        return res.value[-1]

    def __add__(self, other: Result[T]) -> Self:
        self.append(other)
        return self
