from robyn import Robyn
import os

app = Robyn(__file__)

def test_directory_path():
    assert app.directory_path == os.path.dirname(os.path.abspath(__file__))

def test_file_path():
    assert app.file_path == __file__


