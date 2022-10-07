from integration_tests.conftest import test_session
from robyn.env_populator import load_vars, parser
import pathlib
import os
import pytest
import requests



path = pathlib.Path(__file__).parent  

#create robyn.env before test and delete it after test
@pytest.fixture
def env_file():
    CONTENT = "PORT=8080"
    dir = path / "test_dir"
    env_file = dir / "robyn.env"
    env_file.write_text(CONTENT)
    yield
    env_file.unlink()

def test_parser(env_file):
    dir = path / "test_dir"
    env_file = dir / "robyn.env"
    assert list(parser(config_path = env_file)) == [['PORT', '8080']]

def test_load_vars(env_file):
    dir = path / "test_dir"
    env_file = dir / "robyn.env"
    load_vars(variables = parser(config_path = env_file))
    assert os.environ['PORT'] == '8080'


def test_get_request(test_session, env_file):
    dir = path / "test_dir"
    env_file = dir / "robyn.env"
    load_vars(variables = parser(config_path = env_file))
    port = os.environ['PORT'] 
    BASE_URL = f"http://127.0.0.1:{port}"
    res = requests.get(f"{BASE_URL}")
    assert res.status_code == 200
