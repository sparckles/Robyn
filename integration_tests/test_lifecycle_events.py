import os
import pathlib
import signal
import tempfile
import time

import pytest
import requests

from integration_tests.conftest import kill_process, spawn_process
from integration_tests.helpers.http_methods_helpers import get


def test_startup_event_fires(session):
    # The startup handler flips an in-process flag that this endpoint reports,
    # proving the STARTUP event actually ran at runtime (not just that the
    # handler was registered) (#470).
    res = get("/lifecycle/startup")
    assert res.json() == {"startup_completed": True}


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX signal-based graceful shutdown; Windows uses a different mechanism",
)
def test_shutdown_event_fires():
    # The default test harness stops the server with SIGKILL (uncatchable), so we
    # start a dedicated server here, ask it to stop gracefully with SIGINT, and
    # assert the shutdown handler wrote its marker file (#470).
    domain = "127.0.0.1"
    port = 8082
    marker_path = os.path.join(tempfile.gettempdir(), "robyn_shutdown_marker.txt")
    if os.path.exists(marker_path):
        os.remove(marker_path)

    base_routes = os.path.join(pathlib.Path(__file__).parent.resolve(), "base_routes.py")
    env = os.environ.copy()
    env["ROBYN_HOST"] = domain
    env["ROBYN_PORT"] = str(port)
    env["ROBYN_SHUTDOWN_MARKER"] = marker_path

    process = spawn_process(["python3", base_routes])
    try:
        # Wait until the server is accepting connections before signalling it.
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                requests.get(f"http://{domain}:{port}/lifecycle/startup", timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise ConnectionError("server under shutdown test never came up")

        os.killpg(os.getpgid(process.pid), signal.SIGINT)

        # Give the graceful shutdown a moment to run the handler and exit.
        for _ in range(30):
            if os.path.exists(marker_path):
                break
            time.sleep(0.5)

        assert os.path.exists(marker_path), "shutdown handler did not run on SIGINT"
        with open(marker_path) as marker_file:
            assert marker_file.read() == "shut down"
    finally:
        kill_process(process)
        if os.path.exists(marker_path):
            os.remove(marker_path)
