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
        res += result.Simple(3)
        print(res)

    def test_Null(self):
        res = result.NONE
        self.assertRaises(RuntimeError, res.append, result.Simple(1))
        a, b = res
        print(a)

    def test_Error(self):
        res = result.Error()
        res.append(result.Simple(1, [ZeroDivisionError()]))
        a, b = res
        print(a)
