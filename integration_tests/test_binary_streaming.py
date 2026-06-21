import requests

BASE_URL = "http://127.0.0.1:8080"
TIMEOUT = 5

EXPECTED = bytes([0]) * 4 + bytes([1]) * 4 + bytes([2]) * 4


def test_stream_bytes_sync(session):
    """A sync generator yielding bytes streams binary data unchanged (#1236)."""
    r = requests.get(f"{BASE_URL}/stream/bytes", timeout=TIMEOUT)
    assert r.status_code == 200
    assert r.headers.get("Content-Type") == "application/octet-stream"
    assert r.content == EXPECTED


def test_stream_bytes_async(session):
    """An async generator yielding bytes also streams correctly (#1236 + #1219)."""
    r = requests.get(f"{BASE_URL}/stream/bytes_async", timeout=TIMEOUT)
    assert r.status_code == 200
    assert r.content == EXPECTED
