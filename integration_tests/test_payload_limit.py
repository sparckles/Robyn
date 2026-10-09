"""Exercise the configured request-body limit through a real Robyn server."""

import http.client
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import pytest
import requests


@pytest.fixture(scope="module")
def payload_server(tmp_path_factory):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    app = tmp_path_factory.mktemp("payload-app") / "app.py"
    app.write_text(
        "from robyn import Robyn\napp = Robyn(__file__)\n@app.post('/body')\ndef body(request):\n    return {'length': len(request.body)}\napp.start()\n"
    )
    env = dict(os.environ, ROBYN_HOST="127.0.0.1", ROBYN_PORT=str(port), ROBYN_MAX_PAYLOAD_SIZE="16", ROBYN_BROWSER_OPEN="")
    # Match the interpreter and checkout used by the test runner.
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    with (app.parent / "server.log").open("w+") as log:
        process = subprocess.Popen([sys.executable, str(app)], env=env, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(f"payload server exited: {log.read()}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                pytest.fail("payload server did not become ready")
            yield port
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.mark.parametrize("size, expected", [(0, 200), (15, 200), (16, 200), (17, 413)])
@pytest.mark.parametrize("content_type", ["text/plain", "application/octet-stream", "application/json"])
def test_content_length_payload_limit(payload_server, size, expected, content_type):
    with requests.post(f"http://127.0.0.1:{payload_server}/body", data=b"x" * size, headers={"Content-Type": content_type}, timeout=3) as response:
        assert response.status_code == expected
        if expected == 200:
            assert response.json() == {"length": size}


@pytest.mark.parametrize("chunks, expected", [([b"a" * 8, b"b" * 8], 200), ([b"a" * 8, b"b" * 9], 413)])
def test_chunked_payload_limit(payload_server, chunks, expected):
    # A generator forces chunked transfer without a Content-Length header.
    with requests.post(f"http://127.0.0.1:{payload_server}/body", data=iter(chunks), timeout=3) as response:
        assert response.status_code == expected
        if expected == 200:
            assert response.json() == {"length": sum(map(len, chunks))}


def test_malformed_payload_does_not_panic(payload_server):
    with socket.create_connection(("127.0.0.1", payload_server), timeout=3) as client:
        client.sendall(b"POST /body HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\nZ\r\nbad\r\n")
        response = http.client.HTTPResponse(client)
        response.begin()
        assert response.status == 400
        response.close()
    # Rejecting a request must not leave the worker unusable.
    with requests.post(f"http://127.0.0.1:{payload_server}/body", data=b"ok", timeout=3) as response:
        assert response.status_code == 200
        assert response.json() == {"length": 2}
