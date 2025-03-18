from typing import Optional, TypeVar, Generic

T = TypeVar("T")


class Result(Generic[T]):
    value: T
    err: Optional[list[Exception]]
    __slots__ = ("value", "err")

    def __init__(self, value: T, err: list[Exception] = None):
        self.value = value
        self.err = err

    def __getitem__(self, item):
        if item == 0:
            return self.value
        elif item == 1:
            return self.err
        else:
            raise StopIteration

    def append_err(self, e: Exception):
        if self.err is None:
            self.err = list()
        self.err.append(e)

    def extend_err(self, e: list[Exception]):
        if self.err is None:
            self.err = list()
        self.err.extend(e)
