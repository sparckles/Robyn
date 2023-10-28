import os
import pathlib
import signal
import socket
import subprocess
import time
from typing import List
import platform

import pytest
from integration_tests.helpers.network_helpers import get_network_host


def spawn_process(command: List[str]) -> subprocess.Popen:
    if platform.system() == "Windows":
        command[0] = "python"
        process = subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        return process
    process = subprocess.Popen(command, preexec_fn=os.setsid)
    return process


def kill_process(process: subprocess.Popen) -> None:
    if platform.system() == "Windows":
        process.send_signal(signal.CTRL_BREAK_EVENT)
        process.kill()
        return

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass


def start_server(domain: str, port: int, is_dev: bool = False) -> subprocess.Popen:
    """
    Call this method to wait for the server to start
    """
    # Start the server
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    command = ["python3", base_routes]
    if is_dev:
        command.append("--dev")
    process = spawn_process(command)

    # Wait for the server to be reachable
    timeout = 5  # The maximum time we will wait for an answer
    start_time = time.time()
    while True:
        current_time = time.time()
        if current_time - start_time > timeout:
            # Robyn didn't start correctly before timeout, kill the process and exit with an exception
            kill_process(process)
            raise ConnectionError("Could not reach Robyn server")
        try:
            sock = socket.create_connection((domain, port), timeout=5)
            sock.close()
            break  # We were able to reach the server, exit the loop
        except Exception:
            pass
    return process


@pytest.fixture(scope="session")
def session():
    domain = "127.0.0.1"
    port = 8080
    os.environ["ROBYN_HOST"] = domain
    process = start_server(domain, port)
    yield
    kill_process(process)


@pytest.fixture(scope="session")
def default_session():
    domain = "127.0.0.1"
    port = 8080
    process = start_server(domain, port)
    yield
    kill_process(process)


@pytest.fixture(scope="session")
def global_session():
    domain = get_network_host()
    port = 8080
    os.environ["ROBYN_HOST"] = domain
    process = start_server(domain, port)
    yield
    kill_process(process)


@pytest.fixture(scope="session")
def dev_session():
    domain = "127.0.0.1"
    port = 8081
    os.environ["ROBYN_HOST"] = domain
    os.environ["ROBYN_PORT"] = str(port)
    # This doesn't test is_dev=True!!!!
    process = start_server(domain, port)
    yield
    kill_process(process)


@pytest.fixture(scope="session")
def test_session():
    domain = "127.0.0.1"
    port = 8080
    os.environ["ROBYN_HOST"] = domain
    os.environ["ROBYN_PORT"] = str(port)
    process = start_server(domain, port, is_dev=True)
    yield
    kill_process(process)


# create robyn.env before test and delete it after test
@pytest.fixture
def env_file():
    CONTENT = """ROBYN_PORT=8081
    ROBYN_URL=127.0.0.1"""
    path = pathlib.Path(__file__).parent
    env_path = path / "robyn.env"
    env_path.write_text(CONTENT)
    yield
    env_path.unlink()
    del os.environ["ROBYN_PORT"]
    del os.environ["ROBYN_HOST"]
