import os
import socket
import subprocess
import sys
import textwrap
import time

import pytest


pytestmark = pytest.mark.skipif(sys.platform.startswith("win32"), reason="SIGTERM graceful shutdown test is POSIX-only")


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(port: int, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise AssertionError(f"Robyn server exited early with {process.returncode}\nstdout: {stdout!r}\nstderr: {stderr!r}")

        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.1)

    process.kill()
    stdout, stderr = process.communicate()
    raise AssertionError(f"Robyn server did not start on port {port}\nstdout: {stdout!r}\nstderr: {stderr!r}")


def test_sigterm_runs_shutdown_handler(tmp_path):
    port = _get_free_port()
    sentinel_file = tmp_path / "shutdown.txt"
    app_file = tmp_path / "graceful_shutdown_app.py"
    app_file.write_text(
        textwrap.dedent(
            """
            import os
            from pathlib import Path

            from robyn import Robyn

            app = Robyn(__file__)

            @app.get("/")
            def index():
                return "Hello World!"

            @app.shutdown_handler
            def shutdown_handler():
                Path(os.environ["ROBYN_SHUTDOWN_SENTINEL"]).write_text("shutdown")

            if __name__ == "__main__":
                app.start(host="127.0.0.1", port=int(os.environ["ROBYN_PORT"]))
            """
        )
    )

    env = os.environ.copy()
    env["ROBYN_PORT"] = str(port)
    env["ROBYN_SHUTDOWN_SENTINEL"] = str(sentinel_file)

    process = subprocess.Popen([sys.executable, str(app_file)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        _wait_for_server(port, process)
        process.terminate()
        process.wait(timeout=15)

        assert process.returncode == 0
        assert sentinel_file.read_text() == "shutdown"
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate()
