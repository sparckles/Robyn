# from integration_tests.conftest import test_session
from robyn.env_populator import load_vars, parser
import pathlib
import os
import pytest
import requests


path = pathlib.Path(__file__).parent

# create robyn.env before test and delete it after test
@pytest.fixture
def env_file():
    CONTENT = """ROBYN_PORT=8080 
    ROBYN_URL=127.0.0.1"""
    env_path = path / "robyn.env"
    env_path.write_text(CONTENT)
    yield
    env_path.unlink()
    os.unsetenv("ROBYN_PORT")
    os.unsetenv("ROBYN_URL")


# this tests if a connection can be made to the server with the correct port imported from the env file
def test_env_population(test_session, env_file):
    env_path = path / "robyn.env"
    load_vars(variables=parser(config_path=env_path))
    PORT = os.environ["ROBYN_PORT"]
    HOST = os.environ["ROBYN_URL"]
    BASE_URL = f"http://{HOST}:{PORT}"
    res = requests.get(f"{BASE_URL}")
    assert res.status_code == 200
