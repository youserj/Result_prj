import unittest
from StructResult import result


class TestType(unittest.TestCase):

    def test_init(self):
        res = result.Simple[int](1)
        self.assertEqual(res.value, 1)
        self.assertEqual(list(res), [1, None])

    def test_Optional(self):

        def foo() -> result.Simple[int]:
            return result.Simple(None)

    def test_resultList(self):
        res = result.List[int]()
        res.append(result.Simple(1, [ValueError("1")]))
        res.append(result.Simple(2))
        res.append(result.Simple(None, [ZeroDivisionError()]))
        res.append(result.Simple("1"))
        print(res)
