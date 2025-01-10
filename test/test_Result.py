import unittest
from StructResult import Result


class TestType(unittest.TestCase):

    def test_init(self):
        res = Result(1)
        self.assertEqual(res.value, 1)
        self.assertEqual(list(res), [1, None])
