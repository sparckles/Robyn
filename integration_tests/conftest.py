import pytest
import subprocess
import pathlib
import os
import time


@pytest.fixture
def session():
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    process = subprocess.Popen(["python3", base_routes])
    time.sleep(1)
    yield
    process.terminate()


