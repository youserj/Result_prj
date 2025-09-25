import unittest
from src.StructResult.result import Sequence, Option, Simple, OK, Error, NULL


class TestSequence(unittest.TestCase):
    """Tests for Sequence class"""

    def test_basic_creation(self) -> None: 
        """Test basic sequence creation"""
        seq = Sequence(1, "hello", True)
        self.assertEqual(seq.value, (1, "hello", True))
        self.assertIsNone(seq.err)
        self.assertTrue(seq.is_ok())

    def test_type_annotations(self) -> None: 
        """Test strict type annotations"""
        seq_int_str: Sequence[int, str] = Sequence(1, "test")
        seq_mixed: Sequence[int, str, bool] = Sequence(1, "hello", True)

        # Type checking should work
        first: int = seq_int_str.value[0]
        second: str = seq_int_str.value[1]

        self.assertEqual(first, 1)
        self.assertEqual(second, "test")

    def test_empty_sequence(self) -> None: 
        """Test empty sequence creation"""
        seq = Sequence()
        self.assertEqual(seq.value, ())
        self.assertIsNone(seq.err)
        self.assertTrue(seq.is_ok())

    def test_with_errors(self) -> None: 
        """Test sequence with errors"""
        error = ExceptionGroup("test", [ValueError("error1")])
        seq = Sequence(1, "test", err=error)

        self.assertEqual(seq.value, (1, "test"))
        self.assertIs(seq.err, error)
        self.assertFalse(seq.is_ok())

    def test_unwrap_success(self) -> None: 
        """Test successful unwrap"""
        seq = Sequence(1, "hello", 3.14)
        result = seq.unwrap()

        self.assertEqual(result, (1, "hello", 3.14))
        self.assertIsInstance(result, tuple)

    def test_unwrap_failure(self) -> None: 
        """Test unwrap with errors"""
        error = ExceptionGroup("test", [ValueError("error1")])
        seq = Sequence(1, "test", err=error)

        with self.assertRaises(ExceptionGroup) as context:
            seq.unwrap()

        self.assertIs(context.exception, error)

    def test_err_propagation(self) -> None:
        """Test error propagation compatibility"""
        seq = Sequence(1, "test")

        # Should work with ErrorPropagator protocol
        self.assertTrue(hasattr(seq, 'append_e'))
        self.assertTrue(hasattr(seq, 'append_err'))
        self.assertTrue(hasattr(seq, 'propagate_err'))

    def test_collector_protocol(self) -> None: 
        """Test Collector protocol compliance"""
        seq = Sequence(1, "hello")

        # Should support iteration
        values, err = seq.unpack()
        self.assertEqual(values, (1, "hello"))
        self.assertIsNone(err)

        # Should have value attribute
        self.assertTrue(hasattr(seq, 'value'))
        self.assertTrue(hasattr(seq, 'err'))

    def test_result_protocol(self) -> None: 
        """Test Result protocol compliance"""
        seq = Sequence(1, "test")

        self.assertTrue(hasattr(seq, 'is_ok'))
        self.assertTrue(hasattr(seq, 'unwrap'))
        self.assertTrue(seq.is_ok())

    def test_complex_types(self) -> None: 
        """Test sequences with complex types"""
        # Nested sequences
        inner_seq = Sequence("nested")
        outer_seq = Sequence(1, inner_seq, True)

        self.assertEqual(outer_seq.value[0], 1)
        self.assertEqual(outer_seq.value[1].value, ("nested",))
        self.assertEqual(outer_seq.value[2], True)

    def test_equality(self) -> None: 
        """Test sequence equality"""
        seq1 = Sequence(1, "test")
        seq2 = Sequence(1, "test")
        seq3 = Sequence(1, "different")

        # Different instances with same values
        self.assertEqual(seq1.value, seq2.value)
        self.assertNotEqual(seq1.value, seq3.value)

    def test_len_behavior(self) -> None: 
        """Test sequence length behavior"""
        seq_single = Sequence(1)
        seq_multi = Sequence(1, "two", 3.0)

        self.assertEqual(len(seq_single.value), 1)
        self.assertEqual(len(seq_multi.value), 3)

    def test_pattern_matching(self) -> None: 
        """Test sequence pattern matching support"""
        seq = Sequence(1, "hello", True)

        # Basic unpacking
        a, b, c = seq.value
        self.assertEqual(a, 1)
        self.assertEqual(b, "hello")
        self.assertEqual(c, True)

    def test_error_accumulation(self) -> None: 
        """Test error accumulation functionality"""
        seq = Sequence(1, "test")

        # Add first error
        seq.append_e(ValueError("first error"), "context1")
        self.assertIsNotNone(seq.err)
        if seq.err is not None:
            self.assertEqual(len(seq.err.exceptions), 1)

        # Add second error with same message (should merge)
        seq.append_e(TypeError("second error"), "context1")
        if seq.err is not None:
            self.assertEqual(len(seq.err.exceptions), 2)

        # Add error with different message (should nest)
        seq.append_e(RuntimeError("third error"), "context2")
        if seq.err is not None:
            self.assertEqual(seq.err.message, "context2")


class TestSequenceIntegration(unittest.TestCase):
    """Integration tests with other system components"""

    def test_with_simple_collector(self) -> None: 
        """Test integration with Simple collector"""
        simple = Simple(42)
        seq = Sequence(simple.value, "additional")

        self.assertEqual(seq.value, (42, "additional"))
        self.assertTrue(seq.is_ok())

    def test_with_option_collector(self) -> None: 
        """Test integration with Option collector"""
        option = Option(100)  # Assuming Option can be created with value
        seq = Sequence(option.value, "test")

        self.assertEqual(seq.value[0], 100)
        self.assertEqual(seq.value[1], "test")

    def test_error_propagation_from_other_collectors(self) -> None: 
        """Test error propagation from other collectors"""
        # Create a collector with error
        error_collector = Simple(100)
        error_collector.append_e(ValueError("source error"))

        seq = Sequence("start")
        result = seq.propagate_err(error_collector)

        self.assertEqual(result, 100)  # Should return the value
        self.assertIsNotNone(seq.err)  # But errors should be propagated
        if seq.err is not None:
            self.assertEqual(len(seq.err.exceptions), 1)

    def test_with_ok_singleton(self) -> None: 
        """Test integration with OK singleton"""
        seq = Sequence(OK, "regular value")

        self.assertIs(seq.value[0], OK)
        self.assertEqual(seq.value[1], "regular value")
        self.assertTrue(seq.is_ok())


class TestSequenceEdgeCases(unittest.TestCase):
    """Edge case tests for Sequence"""

    def test_none_values(self) -> None: 
        """Test sequences with None values"""
        seq = Sequence(None, "test", None)
        self.assertEqual(seq.value, (None, "test", None))
        self.assertEqual(seq.unwrap(), (None, "test", None))

    def test_large_sequences(self) -> None: 
        """Test sequences with many elements"""
        large_tuple = tuple(range(100))
        seq = Sequence(*large_tuple)
        self.assertEqual(seq.value, large_tuple)
        self.assertEqual(len(seq.value), 100)

    def test_nested_tuples(self) -> None: 
        """Test sequences containing nested tuples"""
        nested = (1, 2, 3)
        seq = Sequence(nested, "test")
        self.assertEqual(seq.value[0], nested)
        self.assertEqual(seq.value[1], "test")

    def test_serialization(self) -> None: 
        """Test basic serialization properties"""
        seq = Sequence(1, "test")

        # Should be picklable
        import pickle
        pickled = pickle.dumps(seq)
        unpickled = pickle.loads(pickled)

        self.assertEqual(unpickled.value, seq.value)
        self.assertEqual(unpickled.err, seq.err)


class TestSequenceAdd(unittest.TestCase):
    """Tests for Sequence.add method"""

    def test_add_simple_value(self) -> None:
        """Test adding Simple value to sequence"""
        seq1: Sequence[int, str] = Sequence(1, "hello")
        simple_val = Simple(3.14)

        seq2 = seq1.add(simple_val)

        self.assertEqual(seq2.value, (1, "hello", 3.14))
        self.assertIsNone(seq2.err)
        self.assertTrue(seq2.is_ok())

    def test_add_ok_singleton(self) -> None:
        """Test adding OK singleton to sequence"""
        seq1: Sequence[int, str] = Sequence(1, "hello")

        seq2 = seq1.add(OK)

        self.assertEqual(seq2.value, (1, "hello", OK))
        self.assertIsNone(seq2.err)
        self.assertTrue(seq2.is_ok())

    def test_add_error(self) -> None:
        """Test adding Error to sequence"""
        seq1: Sequence[int, str] = Sequence(1, "hello")
        error = Error.from_e(ValueError("test error"))

        seq2 = seq1.add(error)

        # Value should include Null for error
        self.assertEqual(seq2.value, (1, "hello", NULL))
        self.assertIsNotNone(seq2.err)
        self.assertFalse(seq2.is_ok())
        if seq2.err:
            self.assertEqual(len(seq2.err.exceptions), 1)

    def test_add_preserves_existing_errors(self) -> None:
        """Test that add preserves errors from original sequence"""
        seq1: Sequence[int, str] = Sequence(1, "hello",
                                            err=ExceptionGroup("original", [ValueError("original error")]))
        simple_val = Simple(3.14)

        seq2 = seq1.add(simple_val)

        self.assertEqual(seq2.value, (1, "hello", 3.14))
        self.assertIsNotNone(seq2.err)
        if seq2.err:
            self.assertEqual(seq2.err.message, "original")
            self.assertEqual(len(seq2.err.exceptions), 1)

    def test_add_merges_errors_from_both_sides(self) -> None:
        """Test that errors from both original and added result are merged"""
        seq1: Sequence[int, str] = Sequence(1, "hello",
                                            err=ExceptionGroup("original", [ValueError("error1")]))
        error_val = Error.from_e(TypeError("error2"), "added")

        seq2 = seq1.add(error_val)

        self.assertEqual(seq2.value, (1, "hello", NULL))
        self.assertIsNotNone(seq2.err)
        # Errors should be merged with proper nesting
        if seq2.err:
            self.assertIsNotNone(seq2.err.subgroup(TypeError))

    def test_add_to_empty_sequence(self) -> None:
        """Test adding to empty sequence"""
        seq1 = Sequence()
        simple_val = Simple("test")

        seq2 = seq1.add(simple_val)

        self.assertEqual(seq2.value, ("test",))
        self.assertIsNone(seq2.err)
        self.assertTrue(seq2.is_ok())

    def test_add_multiple_times(self) -> None:
        """Test chaining multiple add operations"""
        seq = Sequence(1)
        seq = seq.add(Simple("hello"))
        seq = seq.add(Simple(3.14))
        seq = seq.add(OK)

        self.assertEqual(seq.value, (1, "hello", 3.14, OK))
        self.assertIsNone(seq.err)
        self.assertTrue(seq.is_ok())

    def test_add_with_option_type(self) -> None:
        """Test adding Option values"""
        seq1: Sequence[int] = Sequence(1)
        option_val = Option("test")  # Assuming Option works like Simple for value

        seq2 = seq1.add(option_val)

        self.assertEqual(seq2.value, (1, "test"))
        self.assertIsNone(seq2.err)

    def test_type_annotations_after_add(self) -> None:
        """Test that type annotations are correct after add"""
        seq1: Sequence[int, str] = Sequence(1, "hello")

        # Adding Simple should preserve type info
        seq2 = seq1.add(Simple(3.14))
        self.assertEqual(seq2.value[0], 1)  # int
        self.assertEqual(seq2.value[1], "hello")  # str
        self.assertEqual(seq2.value[2], 3.14)  # float

        # Adding OK should work
        seq3 = seq2.add(OK)
        self.assertIs(seq3.value[3], OK)

        # Adding Error should include Null
        seq4 = seq3.add(Error.from_e(ValueError("test")))
        self.assertIs(seq4.value[4], NULL)

    def test_add_error_propagation_behavior(self) -> None:
        """Test that error propagation works correctly in add"""
        # Create a result with error
        error_result = Simple("will error")
        error_result.append_e(ValueError("source error"), "context")

        seq1: Sequence[int] = Sequence(1)
        seq2 = seq1.add(error_result)

        # Should have the error from the added result
        self.assertIsNotNone(seq2.err)
        self.assertEqual(seq2.err.message, "context")
        self.assertEqual(len(seq2.err.exceptions), 1)

    def test_add_preserves_sequence_immutability(self) -> None:
        """Test that original sequence is not modified by add"""
        seq1: Sequence[int, str] = Sequence(1, "hello")
        original_value = seq1.value
        original_err = seq1.err

        seq2 = seq1.add(Simple(3.14))

        # Original should be unchanged
        self.assertEqual(seq1.value, original_value)
        self.assertEqual(seq1.err, original_err)

        # New sequence should be different
        self.assertIsNot(seq1, seq2)
        self.assertEqual(seq2.value, (1, "hello", 3.14))

    def test_add_with_none_values(self) -> None:
        """Test adding results with None values"""
        seq1: Sequence[int] = Sequence(1)
        option_with_none = Option(None)  # Optional value

        seq2 = seq1.add(option_with_none)

        self.assertEqual(seq2.value, (1, None))
        self.assertIsNone(seq2.err)


class TestSequenceAddEdgeCases(unittest.TestCase):
    """Edge case tests for Sequence.add"""

    def test_add_after_error_accumulation(self) -> None:
        """Test adding to sequence that already has multiple errors"""
        seq1 = Sequence(1, "test")
        seq1.append_e(ValueError("error1"), "validation")
        seq1.append_e(TypeError("error2"), "validation")

        seq2 = seq1.add(Simple(3.14))

        self.assertEqual(seq2.value, (1, "test", 3.14))
        self.assertIsNotNone(seq2.err)
        self.assertEqual(len(seq2.err.exceptions), 2)

    def test_add_complex_error_structure(self) -> None:
        """Test adding with complex ExceptionGroup structures"""
        complex_error = ExceptionGroup("complex", [
            ValueError("err1"),
            ExceptionGroup("nested", [TypeError("err2")])
        ])

        seq1 = Sequence(1)
        error_result = Error(complex_error)

        seq2 = seq1.add(error_result)

        self.assertEqual(seq2.value, (1, NULL))
        self.assertIsNotNone(seq2.err)
        # Complex structure should be preserved
        self.assertEqual(seq2.err.message, "complex")

    def test_add_with_custom_collector(self) -> None:
        """Test adding custom collector types"""

        class CustomCollector(Simple[str]):
            def custom_method(self) -> str:
                return self.value.upper()

        custom = CustomCollector("test")
        seq1 = Sequence(1)

        seq2 = seq1.add(custom)

        self.assertEqual(seq2.value, (1, "test"))
        self.assertIsNone(seq2.err)


class TestSequenceAddTypeSafety(unittest.TestCase):
    """Type safety tests for Sequence.add"""

    def test_type_inference_chain(self) -> None:
        """Test that type inference works through add chain"""
        # Start with specific types
        seq: Sequence[int] = Sequence(1)

        # Each add should properly infer new type
        seq = seq.add(Simple("hello"))  # Should be Sequence[int, str]
        self.assertEqual(seq.value[0], 1)
        self.assertEqual(seq.value[1], "hello")

        seq = seq.add(Simple(3.14))  # Should be Sequence[int, str, float]
        self.assertEqual(seq.value[2], 3.14)

        seq = seq.add(OK)  # Should be Sequence[int, str, float, Ok]
        self.assertIs(seq.value[3], OK)

    def test_unwrap_after_add_operations(self) -> None:
        """Test that unwrap works correctly after multiple adds"""
        seq = Sequence(1)
        seq: Sequence[int, str] = seq.add(Simple("test"))
        seq = seq.add(Simple(True))

        result = seq.unwrap()
        self.assertEqual(result, (1, "test", True))
        self.assertIsInstance(result, tuple)


class TestSequenceTyping(unittest.TestCase):
    """Test type annotations are correct"""

    def test_type_annotations(self) -> None: 
        """Test that type annotations work correctly"""
        # These should not cause type errors when checked with mypy/pyright
        seq1: Sequence[int, str] = Sequence(1, "hello")
        seq2: Sequence[int, str, bool] = Sequence(1, "test", True)
        seq3: Sequence[()] = Sequence()  # Empty tuple type

        # Type narrowing should work
        if seq1.is_ok():
            values: tuple[int, str] = seq1.unwrap()
            self.assertEqual(values, (1, "hello"))


def suite() -> unittest.TestSuite:
    """Create test suite"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestSequence))
    test_suite.addTest(unittest.makeSuite(TestSequenceIntegration))
    test_suite.addTest(unittest.makeSuite(TestSequenceEdgeCases))
    test_suite.addTest(unittest.makeSuite(TestSequenceTyping))
    return test_suite
