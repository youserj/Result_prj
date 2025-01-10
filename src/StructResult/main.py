from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class Result:
    value: Any
    err: Optional[list[Exception]] = None

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
