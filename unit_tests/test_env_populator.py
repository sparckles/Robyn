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


def test_parser_skips_blank_and_malformed_lines(tmp_path):
    env_path = tmp_path / "robyn.env"
    env_path.write_text("ROBYN_PORT=8080\n\n   \n# a comment\nNO_EQUALS\n=NO_KEY\nROBYN_HOST=127.0.0.1\n")
    result = list(parser(config_path=env_path))
    assert result == [["ROBYN_PORT", "8080"], ["ROBYN_HOST", "127.0.0.1"]]


def test_parser_preserves_equals_in_value(tmp_path):
    env_path = tmp_path / "robyn.env"
    env_path.write_text("SECRET_KEY=abc=123==\n")
    result = list(parser(config_path=env_path))
    assert result == [["SECRET_KEY", "abc=123=="]]


def test_load_vars_with_blank_line_does_not_crash(tmp_path):
    env_path = tmp_path / "robyn.env"
    env_path.write_text("ROBYN_PORT=8081\n\nROBYN_HOST=0.0.0.0\n")
    saved = {key: os.environ.pop(key, None) for key in ("ROBYN_PORT", "ROBYN_HOST")}
    try:
        load_vars(variables=parser(config_path=env_path))
        assert os.environ["ROBYN_PORT"] == "8081"
        assert os.environ["ROBYN_HOST"] == "0.0.0.0"
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
