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
