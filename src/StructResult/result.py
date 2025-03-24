from typing import Optional, TypeVar, Generic, Self

T = TypeVar("T")


class Simple(Generic[T]):
    value: Optional[T]
    err: Optional[list[Exception]]
    __slots__ = ("value", "err")

    def __init__(self, value: Optional[T], err: list[Exception] = None):
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


NONE = Simple(None)
"""None result"""


class List(Simple, Generic[T]):
    value: list[T]
    __slots__ = ("value", "err")

    def __init__(self):
        super().__init__(list())

    def append(self, res: Simple[T]):
        self.value.append(res.value)
        if res.err is not None:
            self.extend_err(res.err)
