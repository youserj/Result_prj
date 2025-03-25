from typing import Optional, TypeVar, Generic, Self
from abc import ABC, abstractmethod

T = TypeVar("T")

empty = tuple()


class Result(Generic[T], ABC):
    value: Optional[T]
    err: Optional[list[Exception]]
    __slots__ = empty

    def __getitem__(self, item):
        if item == 0:
            return self.value
        elif item == 1:
            return self.err
        else:
            raise StopIteration

    @abstractmethod
    def append(self, res: Self):
        """"""

    def append_err(self, e: Exception):
        if self.err is None:
            self.err = list()
        self.err.append(e)

    def extend_err(self, e: list[Exception]):
        if self.err is None:
            self.err = list()
        self.err.extend(e)


class Simple(Result, Generic[T]):
    value: Optional[T]
    err: Optional[list[Exception]]
    __slots__ = ("value", "err")

    def __init__(self, value: Optional[T] = None, err: list[Exception] = None):
        self.value = value
        self.err = err

    def append(self, res: Result):
        """set value and append errors"""
        self.value = res.value
        if res.err is not None:
            self.extend_err(res.err)


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
    err: Optional[list[Exception]]
    __slots__ = ("err",)

    def __init__(self, err: list[Exception] = None):
        self.err = err

    def append(self, res: Result):
        if res.err is not None:
            self.extend_err(res.err)

    @property
    def value(self):
        return None


class List(Result, Generic[T]):
    value: list[T]
    __slots__ = ("value", "err")

    def __init__(self, err: list[Exception] = None):
        self.value = list()
        self.err = err

    def append(self, res: Result[T]):
        """append value and errors"""
        self.value.append(res.value)
        if res.err is not None:
            self.extend_err(res.err)

    def __add__(self, other: Result[T]) -> Self:
        self.append(other)
        return self
