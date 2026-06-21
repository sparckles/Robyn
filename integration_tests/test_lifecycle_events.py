import os
import pathlib
import signal
import subprocess
import tempfile
import time

import pytest
import requests

from integration_tests.conftest import kill_process
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
    # Start a dedicated server, ask it to stop gracefully with SIGINT, and assert
    # the shutdown handler wrote its marker file (#470). The default harness stops
    # servers with SIGKILL (uncatchable), so shutdown can only be observed here.
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

    # Spawn directly (not via the conftest helper) so we can pass `env` and put the
    # child in its own process group for a clean SIGINT.
    process = subprocess.Popen(["python3", base_routes], env=env, preexec_fn=os.setsid)
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
        for _ in range(16):
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
