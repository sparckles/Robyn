from robyn.env_populator import load_vars, parser
import pathlib
import os

# content of test_tmp_path.py
CONTENT = "PORT=8080"

path = pathlib.Path(__file__).parent  

#create a directory before test and delete it after test
def test_create_file():
    d = path / "test_dir"
    p = d / "robyn.env"
    p.write_text(CONTENT)

def test_parser():
    d = path / "test_dir"
    p = d / "robyn.env"
    assert list(parser(config_path = p)) == [['PORT', '8080']]

def test_load_vars():
    d = path / "test_dir"
    p = d / "robyn.env"
    load_vars(variables = parser(config_path = p))
    assert os.environ['PORT'] == '8080'

#delete the file after test
def test_delete_file():
    d = path / "test_dir"
    p = d / "robyn.env"
    p.unlink()
    