import signal
import sys
from typing import List
import pytest
import subprocess
import pathlib
import os
import time


def spawn_process(command: List[str]) -> subprocess.Popen:
    if sys.platform.startswith("win32"):
        command[0] = "python"
        process = subprocess.Popen(
            command, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        return process
    process = subprocess.Popen(command, preexec_fn=os.setsid)
    return process


def kill_process(process: subprocess.Popen) -> None:
    if sys.platform.startswith("win32"):
        process.send_signal(signal.CTRL_BREAK_EVENT)
        process.kill()
        return
    
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass

@pytest.fixture(scope="session")
def session():
    os.environ["ROBYN_URL"] = "127.0.0.1"
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    command = ["python3", base_routes]
    process = spawn_process(command)
    time.sleep(5)
    yield
    kill_process(process)


@pytest.fixture(scope="session")
def default_session():
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    command = ["python3", base_routes]
    process = spawn_process(command)
    time.sleep(5)
    yield
    kill_process(process)


@pytest.fixture(scope="session")
def global_session():
    os.environ["ROBYN_URL"] = "0.0.0.0"
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    command = ["python3", base_routes]
    process = spawn_process(command)
    time.sleep(1)
    yield
    kill_process(process)


@pytest.fixture(scope="session")
def dev_session():
    os.environ["ROBYN_URL"] = "127.0.0.1"
    os.environ["ROBYN_PORT"] = "5001"
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    command = ["python3", base_routes, "--dev"]
    process = spawn_process(command)
    time.sleep(5)
    yield
    kill_process(process)


@pytest.fixture(scope="session")
def test_session():
    os.environ["ROBYN_URL"] = "127.0.0.1"
    os.environ["ROBYN_PORT"] = "8080"
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    command = ["python3", base_routes, "--dev"]
    process = spawn_process(command)
    time.sleep(5)
    yield
    kill_process(process)
