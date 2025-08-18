import unittest
from unittest.mock import patch
from typing import Optional, Any
from src.StructResult.result import Simple, Bool, Ok, OK, Error, List


class TestResultSystem(unittest.TestCase):
    def test_ok_singleton(self) -> None:
        self.assertTrue(OK.is_ok())
        self.assertIsInstance(OK, Ok)

    def test_error_creation(self) -> None:
        exc = ValueError("test error")
        err = Error(exc, "context")
        self.assertFalse(err.is_ok())
        self.assertIsNotNone(err.err)
        self.assertEqual(err.msg, "context")
        self.assertEqual(len(err.err.exceptions), 1)
        self.assertIsInstance(err.err.exceptions[0], ValueError)

    def test_simple_success(self) -> None:
        res = Simple[str]("test", value="success")
        self.assertTrue(res.is_ok())
        self.assertEqual(res.unwrap(), "success")
        self.assertIsNone(res.err)

    def test_simple_failure(self) -> None:
        exc = TypeError("type error")
        res = Simple[str]("test").append_err(exc)
        self.assertFalse(res.is_ok())
        self.assertIsNotNone(res.err)
        with self.assertRaises(ExceptionGroup):
            res.unwrap()

    def test_bool_type(self) -> None:
        true_res = Bool("test", value=True)
        false_res = Bool("test", value=False)
        self.assertTrue(true_res.unwrap())
        self.assertFalse(false_res.unwrap())

    def test_error_propagation(self) -> None:
        exc1 = RuntimeError("error 1")
        exc2 = KeyError("error 2")
        res1 = Simple[int]("op1").append_err(exc1)
        res2 = Simple[int]("op2").append_err(exc2)
        res1.propagate_err(res2)
        self.assertFalse(res1.is_ok())
        if res1.err is not None:
            self.assertEqual(len(res1.err.exceptions), 2)
            self.assertIsInstance(res1.err.exceptions[0], RuntimeError)
            self.assertIsInstance(res1.err.exceptions[1].exceptions[0], KeyError)

    def test_list_collector(self) -> None:
        lst = List[int]("collection")
        lst.append(Simple[int]("item1", value=42))
        lst.append(Error(ValueError("bad value"), "item2"))
        lst.append(OK)
        lst.append(Simple[int]("item3", value=100))
        self.assertEqual(len(lst.value), 4)
        self.assertEqual(lst.value[0], 42)
        self.assertIsInstance(lst.value[2], Ok)
        self.assertEqual(lst.value[3], 100)
        self.assertFalse(lst.is_ok())
        self.assertEqual(len(lst.err.exceptions), 1)
        self.assertIsInstance(lst.err.exceptions[0].exceptions[0], ValueError)

    def test_list_operator_overload(self) -> None:
        lst = List[str]("test") + Simple[str]("first", value="hello")
        lst += Error(TypeError("type error"), "second")
        self.assertEqual(len(lst.value), 2)
        self.assertEqual(lst.value[0], "hello")
        self.assertFalse(lst.is_ok())

    def test_exception_group_merging(self) -> None:
        exc1 = ValueError("val1")
        exc2 = TypeError("type1")
        exc3 = KeyError("key1")
        res1 = Simple[None]("group1").append_err(exc1).append_err(exc2)
        res2 = Simple[None]("group1").append_err(exc3)
        res1.propagate_err(res2)
        self.assertEqual(len(res1.err.exceptions), 3)
        self.assertEqual(res1.err.message, "group1")

    def test_different_error_groups(self) -> None:
        exc1 = ValueError("val1")
        exc2 = TypeError("type1")
        res1 = Simple[None]("group1").append_err(exc1)
        res2 = Simple[None]("group2").append_err(exc2)
        res1.propagate_err(res2)
        self.assertEqual(len(res1.err.exceptions), 2)
        self.assertIsInstance(res1.err.exceptions[1], ExceptionGroup)

    def test_set_operation(self) -> None:
        main = Simple[str]("main")
        other = Simple[str]("other", value="data")
        result = main.set(other)
        self.assertEqual(main.value, "data")
        self.assertEqual(result, "data")
        self.assertTrue(main.is_ok())

    def test_bool_set_operation(self) -> None:
        main = Bool("main")
        other = Bool("other", value=True)
        result = main.set(other)
        self.assertTrue(main.value)
        self.assertTrue(result)

    def test_simple_none_value(self) -> None:
        res = Simple[Optional[int]]("test", value=None)
        self.assertTrue(res.is_ok())
        self.assertIsNone(res.unwrap())

    def test_bool_false_with_error(self) -> None:
        res = Bool("test", value=False)
        res.append_err(ValueError("bool error"))
        self.assertFalse(res.value)
        self.assertFalse(res.is_ok())
        with self.assertRaises(ExceptionGroup):
            res.unwrap()

    def test_nested_exception_groups(self) -> None:
        inner_group = ExceptionGroup("inner", [ValueError("v1"), TypeError("t1")])
        outer_group = ExceptionGroup("outer", [inner_group, KeyError("k1")])
        res = Simple[int]("test").append_err(outer_group)
        if res.err is not None:
            self.assertEqual(len(res.err.exceptions), 1)
            self.assertIsInstance(res.err.exceptions[0], ExceptionGroup)
            self.assertEqual(res.err.exceptions[0].message, "outer")
            self.assertEqual(res.err.exceptions[0].exceptions[0].message, "inner")

    def test_list_empty(self) -> None:
        lst = List[str]("empty")
        self.assertTrue(lst.is_ok())
        self.assertEqual(len(lst.value), 0)
        self.assertIsNone(lst.err)

    def test_list_mixed_types(self) -> None:
        lst = List[object]("mixed")
        lst.append(Simple[int]("int", value=42))
        lst.append(Simple[str]("str", value="hello"))
        lst.append(Error(ValueError("error"), "error"))
        self.assertEqual(len(lst.value), 3)
        self.assertEqual(lst.value[0], 42)
        self.assertEqual(lst.value[1], "hello")
        self.assertIsInstance(lst.value[2], type(None))

    def test_propagate_none(self) -> None:
        res = Simple[int]("main", value=42)
        res.propagate_err(Simple[int]("other"))
        self.assertTrue(res.is_ok())
        self.assertEqual(res.unwrap(), 42)

    def test_type_hints(self) -> None:
        def processor() -> Simple[str]:
            return Simple[str]("processor", value="result")

        result = processor()
        value: str = result.unwrap()
        self.assertEqual(value, "result")

    def test_combined_workflow(self) -> None:
        main = List[int]("combined workflow")
        main += Simple[int]("op1", value=10)
        main += Simple[int]("op2", value=20)
        main += Error(ValueError("invalid value"), "op3")
        main += Simple[int]("op4", value=30)
        self.assertEqual(len(main.value), 4)
        self.assertEqual(main.value[0], 10)
        self.assertEqual(main.value[1], 20)
        self.assertEqual(main.value[3], 30)
        self.assertFalse(main.is_ok())
        self.assertEqual(len(main.err.exceptions), 1)
        with self.assertRaises(ExceptionGroup):
            main.unwrap()

    def test_multiple_propagations(self) -> None:
        res1 = Simple[int]("first").append_err(ValueError("v1"))
        res2 = Simple[int]("second").append_err(TypeError("t1"))
        res3 = Simple[int]("third").append_err(KeyError("k1"))

        main = Simple[int]("main")
        main.propagate_err(res1)
        main.propagate_err(res2)
        main.propagate_err(res3)

        self.assertEqual(len(main.err.exceptions), 3)

    @patch.object(Simple, "append_err")
    def test_propagate_err_calls(self, mock_append: Any) -> None:
        err_res = Simple[int]("error")
        err_res.err = ExceptionGroup("error", [ValueError("test")])
        main = Simple[int]("main")
        main.propagate_err(err_res)
        mock_append.assert_called_once_with(err_res.err)

    def test_iterator_protocol(self) -> None:
        res = Simple[str]("iter", value="test")
        values = list(res)
        self.assertEqual(len(values), 2)
        self.assertEqual(values[0], "test")
        self.assertIsNone(values[1])

    def test_bool_truthiness(self) -> None:
        true_res = Bool("true", value=True)
        false_res = Bool("false", value=False)
        self.assertTrue(true_res.value)
        self.assertFalse(false_res.value)
        self.assertTrue(bool(true_res.unwrap()))
        self.assertFalse(bool(false_res.unwrap()))

    def test_equal(self):
        res = Simple("1")
        group = ExceptionGroup("1", (ValueError("1"),))
        res.append_err(group)
        self.assertEqual(res.err, group)
