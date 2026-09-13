import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
_PARSER = _ROOT / "robyn" / "argument_parser.py"
_spec = importlib.util.spec_from_file_location("robyn_argument_parser", _PARSER)
_parser = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_parser)

is_production_log_level = _parser.is_production_log_level
Config = _parser.Config


class LogLevelTests(unittest.TestCase):
    def test_warning_and_warn_are_production_levels(self):
        self.assertTrue(is_production_log_level("WARNING"))
        self.assertTrue(is_production_log_level("WARN"))
        self.assertTrue(is_production_log_level("warning"))
        self.assertTrue(is_production_log_level("warn"))

    def test_info_and_debug_are_not_production_levels(self):
        self.assertFalse(is_production_log_level("INFO"))
        self.assertFalse(is_production_log_level("DEBUG"))
        self.assertFalse(is_production_log_level(None))

    def test_cli_warning_matches_cli_warn(self):
        with patch.object(sys, "argv", ["robyn", "--log-level", "WARNING"]):
            warning_config = Config()
        with patch.object(sys, "argv", ["robyn", "--log-level", "WARN"]):
            warn_config = Config()
        self.assertTrue(is_production_log_level(warning_config.log_level))
        self.assertTrue(is_production_log_level(warn_config.log_level))

    def test_fast_mode_defaults_to_a_production_log_level(self):
        with patch.object(sys, "argv", ["robyn", "--fast"]):
            config = Config()
        self.assertEqual(config.log_level, "WARNING")
        self.assertTrue(is_production_log_level(config.log_level))


if __name__ == "__main__":
    unittest.main()
