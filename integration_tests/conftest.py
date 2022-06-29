import pytest
import subprocess
import pathlib
import os
import time


@pytest.fixture
def session():
    os.environ["ROBYN_URL"] = "127.0.0.1"
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    process = subprocess.Popen(["python3", base_routes])
    time.sleep(5)
    yield
    process.terminate()


@pytest.fixture
def default_session():
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    process = subprocess.Popen(["python3", base_routes])
    time.sleep(5)
    yield
    process.terminate()


@pytest.fixture
def global_session():
    os.environ["ROBYN_URL"] = "0.0.0.0"
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    process = subprocess.Popen(["python3", base_routes])
    time.sleep(1)
    yield
    process.terminate()


@pytest.fixture(scope="session")
def dev_session():
    os.environ["ROBYN_URL"] = "127.0.0.1"
    os.environ["ROBYN_PORT"] = "5001"
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    process = subprocess.Popen(["python3", base_routes, "--dev"])
    time.sleep(5)
    yield
    process.terminate()

