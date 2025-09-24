import unittest
from src.StructResult.result import Sequence, Option, Simple, OK


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
        values, err = tuple(seq)
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


def suite():
    """Create test suite"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestSequence))
    test_suite.addTest(unittest.makeSuite(TestSequenceIntegration))
    test_suite.addTest(unittest.makeSuite(TestSequenceEdgeCases))
    test_suite.addTest(unittest.makeSuite(TestSequenceTyping))
    return test_suite
