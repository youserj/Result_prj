import traceback
import unittest
from StructResult import result


class TestType(unittest.TestCase):

    def test_init(self):
        res = result.Simple[int](1, msg="handle")
        res.append_err(ExceptionGroup("handle1", [ValueError(2)]))
        res.append_err(ValueError(1))
        self.assertEqual(res.value, 1)
        traceback.print_exception(res.err)

    def test_Optional(self):

        def foo() -> result.Simple[int]:
            return result.Simple(None)

    def test_resultList(self):
        res = result.List[int]("list")
        res.append(result.Simple(1, ValueError(1)))
        res.append_err(ValueError(2))
        res.append(result.Simple(2))
        res.append(result.Simple(None, ZeroDivisionError(3), msg="devide"))
        res.append(result.Simple("1"))
        res += result.Simple(3, TypeError(13), msg="type")
        traceback.print_exception(res.err)

    def test_Null(self):
        res = result.NONE
        self.assertRaises(RuntimeError, res.append, result.Simple(1))
        a, b = res
        print(a)

    def test_Error(self):
        res = result.Error()
        res.append(result.Simple(1, ZeroDivisionError()))
        a, b = res
        print(a)

    def test_simple_append_value(self):
        # Test appending a successful Simple result
        res1 = result.Simple(10)
        res2 = result.Simple(20)
        res1.append(res2)
        self.assertEqual(res1.value, 20)
        self.assertIsNone(res1.err)

    def test_simple_append_error(self):
        # Test appending an error Simple result
        res1 = result.Simple(10)
        res2 = result.Simple(e=ValueError("test error"), msg="test")
        res1.append(res2)
        self.assertEqual(res1.value, None)
        self.assertIsNotNone(res1.err)
        self.assertEqual(len(res1.err.exceptions), 1)

    def test_simple_append_multiple_errors(self):
        # Test error aggregation
        res1 = result.Simple(e=TypeError("type error"), msg="test")
        res2 = result.Simple(e=ValueError("value error"), msg="test")
        res1.append(res2)
        self.assertEqual(len(res1.err.exceptions), 2)

    def test_simple_append_different_messages(self):
        # Test error aggregation with different messages
        res1 = result.Simple(e=TypeError("type error"), msg="test1")
        res2 = result.Simple(e=ValueError("value error"), msg="test2")
        res1.append(res2)
        # Should nest the exception groups
        self.assertEqual(len(res1.err.exceptions), 2)
        self.assertIsInstance(res1.err.exceptions[1], ExceptionGroup)

    def test_null_append(self):
        # Test that Null can't be appended to
        with self.assertRaises(RuntimeError):
            result.NONE.append(result.Simple(10))

    def test_error_append_value(self):
        # Test that Error ignores values but collects errors
        err1 = result.Error(e=ValueError("error1"), msg="test")
        simple = result.Simple(10)
        err1.append(simple)
        self.assertIsNone(err1.value)

    def test_error_append_error(self):
        # Test error aggregation in Error class
        err1 = result.Error(e=ValueError("error1"), msg="test")
        err2 = result.Error(e=TypeError("error2"), msg="test")
        err1.append(err2)
        self.assertEqual(len(err1.err.exceptions), 2)

    def test_list_append_values(self):
        # Test value collection in List
        lst = result.List[int]()
        lst.append(result.Simple(1))
        lst.append(result.Simple(2))
        lst.append(result.Simple(3))
        self.assertEqual(lst.value, [1, 2, 3])
        self.assertIsNone(lst.err)

    def test_list_append_mixed(self):
        # Test mixed success and error cases
        lst = result.List[int](msg="test")
        lst.append(result.Simple(1))
        lst.append(result.Simple(e=ValueError("error1")))
        lst.append(result.Simple(2))
        lst.append(result.Simple(e=TypeError("error2")))
        self.assertEqual(lst.value, [1, None, 2, None])
        self.assertEqual(len(lst.err.exceptions), 2)

    def test_list_operator_overload(self):
        # Test the __add__ operator
        lst = result.List[int]()
        lst += result.Simple(1)
        lst = lst + result.Simple(2)
        self.assertEqual(lst.value, [1, 2])

    def test_type_safety(self):
        # Test type safety (should ideally fail but currently doesn't)
        lst = result.List[int]()
        lst.append(result.Simple("string"))  # This should ideally raise TypeError
        self.assertEqual(lst.value, ["string"])

    def test_type_return(self):
        res1 = result.Result[str]()
        res2 = result.Result[int]()
        res3: int = res1.propagate_err(res2)
        err_res = result.Error()
        res4: int = err_res.append(res2)

