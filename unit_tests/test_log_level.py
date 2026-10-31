import logging
import sys
from unittest.mock import patch

import pytest

from robyn.argument_parser import Config, is_production_log_level


@pytest.mark.parametrize("level", ["WARNING", "WARN", "warning", "warn", "ERROR", "CRITICAL", "FATAL", logging.WARNING, logging.ERROR])
def test_production_log_levels(level):
    assert is_production_log_level(level)


@pytest.mark.parametrize("level", ["INFO", "DEBUG", "NOTSET", "info", "", None, "BOGUS", logging.INFO])
def test_non_production_log_levels(level):
    assert not is_production_log_level(level)


@pytest.mark.parametrize("flag", ["WARNING", "WARN", "warning", "Error"])
def test_cli_log_level_is_normalised_and_accepted_by_logging(flag):
    with patch.object(sys, "argv", ["robyn", "--log-level", flag]):
        config = Config()
    assert config.log_level == flag.upper()
    assert is_production_log_level(config.log_level)
    # logging.basicConfig rejects lower-case names; the normalised value must not.
    logging.getLogger("robyn.test").setLevel(config.log_level)


def test_fast_mode_defaults_to_a_production_log_level():
    with patch.object(sys, "argv", ["robyn", "--fast"]):
        config = Config()
    assert config.log_level == "WARNING"
    assert is_production_log_level(config.log_level)


def test_default_and_dev_log_levels_are_verbose():
    with patch.object(sys, "argv", ["robyn"]):
        assert Config().log_level == "INFO"
    with patch.object(sys, "argv", ["robyn", "--dev"]):
        assert Config().log_level == "DEBUG"
    assert not is_production_log_level("INFO")
    assert not is_production_log_level("DEBUG")
