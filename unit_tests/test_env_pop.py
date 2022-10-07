from robyn.env_populator import load_vars, parser
import pathlib
import os
import pytest




path = pathlib.Path(__file__).parent  

#create robyn.env before test and delete it after test
@pytest.fixture
def env_file():
    CONTENT = """ROBYN_PORT=8080 
    ROBYN_URL=127.0.1.1"""
    dir = path / "test_dir"
    env_file = dir / "robyn.env"
    env_file.write_text(CONTENT)
    yield
    env_file.unlink()
    os.unsetenv("ROBYN_PORT")
    os.unsetenv("ROBYN_URL")

def test_parser(env_file):
    dir = path / "test_dir"
    env_file = dir / "robyn.env"
    assert list(parser(config_path = env_file)) == [['ROBYN_PORT', '8080'], ['ROBYN_URL', '127.0.1.1']]

def test_load_vars(env_file):
    dir = path / "test_dir"
    env_file = dir / "robyn.env"
    load_vars(variables = parser(config_path = env_file))
    assert os.environ['ROBYN_PORT'] == '8080'
    assert os.environ['ROBYN_URL'] == '127.0.1.1'