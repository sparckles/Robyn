import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "robyn"))

from env_populator import env_bool


class EnvBoolTests(unittest.TestCase):
    def test_false_string_is_false(self):
        self.assertFalse(env_bool("False"))
        self.assertFalse(env_bool("false"))
        self.assertFalse(env_bool("0"))
        self.assertFalse(env_bool("no"))

    def test_true_strings(self):
        self.assertTrue(env_bool("True"))
        self.assertTrue(env_bool("true"))
        self.assertTrue(env_bool("1"))
        self.assertTrue(env_bool("yes"))
        self.assertTrue(env_bool(" YES "))

    def test_unset_keeps_default(self):
        self.assertFalse(env_bool(None, False))
        self.assertTrue(env_bool(None, True))


if __name__ == "__main__":
    unittest.main()
