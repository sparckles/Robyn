import logging
import os
import pathlib

import pytest

from robyn.env_populator import load_vars, parser


@pytest.fixture
def env_file():
    CONTENT = """ROBYN_PORT=8080
ROBYN_HOST=127.0.0.1"""
    path = pathlib.Path(__file__).parent
    env_path = path / "robyn.env"
    env_path.write_text(CONTENT)
    yield
    env_path.unlink()
    # Clean up environment variables if they exist
    if "ROBYN_PORT" in os.environ:
        del os.environ["ROBYN_PORT"]
    if "ROBYN_HOST" in os.environ:
        del os.environ["ROBYN_HOST"]


# this tests if a connection can be made to the server with the correct port imported from the env file
@pytest.mark.benchmark
def test_env_population(env_file):
    # Clean up environment variables before test to ensure fresh state
    if "ROBYN_PORT" in os.environ:
        del os.environ["ROBYN_PORT"]
    if "ROBYN_HOST" in os.environ:
        del os.environ["ROBYN_HOST"]

    path = pathlib.Path(__file__).parent
    env_path = path / "robyn.env"
    load_vars(variables=parser(config_path=env_path))
    PORT = os.environ["ROBYN_PORT"]
    HOST = os.environ["ROBYN_HOST"]
    assert PORT == "8080"
    assert HOST == "127.0.0.1"


def test_parser_skips_blank_and_malformed_lines(tmp_path, caplog):
    env_path = tmp_path / "robyn.env"
    env_path.write_text("ROBYN_PORT=8080\n\n   \n# a comment\nNO_EQUALS\n=NO_KEY\nROBYN_HOST=127.0.0.1\n")
    with caplog.at_level(logging.WARNING, logger="robyn.env_populator"):
        result = list(parser(config_path=env_path))
    assert result == [["ROBYN_PORT", "8080"], ["ROBYN_HOST", "127.0.0.1"]]
    assert "malformed line 5" in caplog.text
    assert "malformed line 6" in caplog.text


def test_parser_never_logs_malformed_line_contents(tmp_path, caplog):
    env_path = tmp_path / "robyn.env"
    env_path.write_text("=hunter2\nAPI_TOKEN hunter2\n")
    with caplog.at_level(logging.WARNING, logger="robyn.env_populator"):
        assert list(parser(config_path=env_path)) == []
    assert "hunter2" not in caplog.text


def test_parser_strips_whitespace_around_key_and_value(tmp_path):
    env_path = tmp_path / "robyn.env"
    env_path.write_text("ROBYN_PORT = 8080\nROBYN_HOST=127.0.0.1   \n")
    assert list(parser(config_path=env_path)) == [["ROBYN_PORT", "8080"], ["ROBYN_HOST", "127.0.0.1"]]


def test_parser_preserves_equals_in_value(tmp_path):
    env_path = tmp_path / "robyn.env"
    env_path.write_text("SECRET_KEY=abc=123==\n")
    result = list(parser(config_path=env_path))
    assert result == [["SECRET_KEY", "abc=123=="]]


def test_load_vars_with_blank_line_does_not_crash(tmp_path, caplog):
    env_path = tmp_path / "robyn.env"
    env_path.write_text("ROBYN_PORT=8081\n\nROBYN_HOST=0.0.0.0\nSECRET_KEY=abc=123==\n")
    saved = {key: os.environ.pop(key, None) for key in ("ROBYN_PORT", "ROBYN_HOST", "SECRET_KEY")}
    try:
        with caplog.at_level(logging.INFO, logger="robyn.env_populator"):
            load_vars(variables=parser(config_path=env_path))
        assert os.environ["ROBYN_PORT"] == "8081"
        assert os.environ["ROBYN_HOST"] == "0.0.0.0"
        assert os.environ["SECRET_KEY"] == "abc=123=="
        # Values may be secrets; only the variable name is logged.
        assert "SECRET_KEY" in caplog.text
        assert "abc=123==" not in caplog.text
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
