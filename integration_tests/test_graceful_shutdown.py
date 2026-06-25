import os
import socket
import subprocess
import sys
import tempfile
import time

import pytest

APP = os.path.join(os.path.dirname(__file__), "graceful_shutdown_app.py")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_serving(proc: subprocess.Popen, port: int, timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with socket.create_connection(("127.0.0.1", port), 0.3):
                return True
        except OSError:
            time.sleep(0.2)
    return False


@pytest.mark.skipif(sys.platform.startswith("win32"), reason="SIGTERM is not delivered on Windows")
def test_sigterm_triggers_graceful_shutdown():
    """SIGTERM should stop the server cleanly and run shutdown handlers (regression for #1324)."""
    sentinel = tempfile.mktemp(prefix="robyn_graceful_")
    port = _free_port()
    proc = subprocess.Popen([sys.executable, APP, sentinel, str(port)])
    try:
        assert _wait_until_serving(proc, port), "server failed to start"

        proc.terminate()  # SIGTERM
        try:
            returncode = proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("server hung after SIGTERM instead of shutting down (#1324)")

        assert returncode == 0, f"expected a clean exit on SIGTERM, got returncode={returncode}"
        assert os.path.exists(sentinel), "shutdown handler did not run on SIGTERM"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        if os.path.exists(sentinel):
            os.remove(sentinel)
