"""
Integration tests for CORS preflight (OPTIONS) handling.

Regression test for https://github.com/sparckles/robyn/issues/1346
These tests spin up a real Robyn server with ALLOW_CORS enabled and make
actual HTTP requests — no TestClient.
"""

import os
import pathlib
import signal
import socket
import subprocess
import time

import pytest
import requests

CORS_PORT = 8083
CORS_HOST = "127.0.0.1"
CORS_BASE_URL = f"http://{CORS_HOST}:{CORS_PORT}"
REQUEST_TIMEOUT = 5

ALLOWED_ORIGIN = "http://localhost:3000"
DISALLOWED_ORIGIN = "http://evil.example.com"


def _start_cors_server():
    app_path = os.path.join(pathlib.Path(__file__).parent.resolve(), "cors_app.py")
    env = os.environ.copy()
    env["ROBYN_HOST"] = CORS_HOST
    env["ROBYN_PORT"] = str(CORS_PORT)

    process = subprocess.Popen(
        ["python3", app_path],
        env=env,
        preexec_fn=os.setsid,
    )

    timeout = 15
    start = time.time()
    while True:
        if process.poll() is not None:
            raise RuntimeError(f"CORS server exited early with code {process.returncode}")
        if time.time() - start > timeout:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            raise ConnectionError(f"CORS server didn't start on {CORS_HOST}:{CORS_PORT}")
        try:
            sock = socket.create_connection((CORS_HOST, CORS_PORT), timeout=2)
            sock.close()
            break
        except Exception:
            time.sleep(0.5)

    time.sleep(1)
    return process


@pytest.fixture(scope="module")
def cors_server():
    process = _start_cors_server()
    yield
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass


# ---------------------------------------------------------------------------
# Preflight (OPTIONS) tests
# ---------------------------------------------------------------------------


def test_options_preflight_returns_204_with_cors_headers(cors_server):
    """Browser sends OPTIONS preflight; server must return 204 with all CORS headers."""
    resp = requests.options(
        f"{CORS_BASE_URL}/data",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization",
        },
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code == 204
    assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
    assert "POST" in resp.headers["Access-Control-Allow-Methods"]
    assert resp.headers["Access-Control-Allow-Credentials"] == "true"


def test_options_preflight_no_duplicate_allow_origin(cors_server):
    """
    Regression: ensure Access-Control-Allow-Origin appears exactly once.
    Duplicate values cause browsers to reject the preflight (Fetch spec).
    """
    resp = requests.options(
        f"{CORS_BASE_URL}/",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
        timeout=REQUEST_TIMEOUT,
    )
    raw_headers = resp.raw.headers if hasattr(resp.raw, "headers") else resp.headers

    origin_values = raw_headers.getall("Access-Control-Allow-Origin", None) if hasattr(raw_headers, "getall") else None

    if origin_values is not None:
        assert len(origin_values) == 1, f"Access-Control-Allow-Origin appeared {len(origin_values)} times: {origin_values}"

    assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN


def test_options_preflight_disallowed_origin_returns_403(cors_server):
    """Origins not in the allowed list should be rejected."""
    resp = requests.options(
        f"{CORS_BASE_URL}/data",
        headers={
            "Origin": DISALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Normal request tests (non-preflight)
# ---------------------------------------------------------------------------


def test_get_with_allowed_origin_has_cors_headers(cors_server):
    """Normal GET from an allowed origin should carry CORS response headers."""
    resp = requests.get(
        f"{CORS_BASE_URL}/",
        headers={"Origin": ALLOWED_ORIGIN},
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code == 200
    allow_origin = resp.headers.get("Access-Control-Allow-Origin")
    assert allow_origin is not None
    assert "Access-Control-Allow-Methods" in resp.headers


def test_get_without_origin_still_has_global_cors_headers(cors_server):
    """Requests without Origin (e.g. curl, Postman) should still get global CORS headers."""
    resp = requests.get(f"{CORS_BASE_URL}/", timeout=REQUEST_TIMEOUT)
    assert resp.status_code == 200
    assert "Access-Control-Allow-Methods" in resp.headers


def test_post_with_allowed_origin(cors_server):
    """POST from allowed origin should succeed with CORS headers."""
    resp = requests.post(
        f"{CORS_BASE_URL}/data",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Content-Type": "application/json",
        },
        data="{}",
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code == 200


def test_custom_response_headers_not_clobbered_by_globals(cors_server):
    """Route-level headers set by the handler should not be overwritten by globals."""
    resp = requests.get(
        f"{CORS_BASE_URL}/custom-header",
        headers={"Origin": ALLOWED_ORIGIN},
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.headers.get("x-custom") == "hello"
    assert "Access-Control-Allow-Methods" in resp.headers
