import unittest
from StructResult import Result, ResultList


class TestType(unittest.TestCase):

    def test_init(self):
        res = Result[int](1)
        self.assertEqual(res.value, 1)
        self.assertEqual(list(res), [1, None])

    def test_Optional(self):

        def foo() -> Result[int]:
            return Result(None)

    def test_ResultList(self):
        res = ResultList[int]()
        res.append(Result(1, [ValueError("1")]))
        res.append(Result(2))
        res.append(Result(None, [ZeroDivisionError()]))
        res.append(Result("1"))
        print(res)
