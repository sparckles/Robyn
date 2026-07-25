import requests

from integration_tests.helpers.http_methods_helpers import BASE_URL

COMPRESSION_BASE_URL = "http://127.0.0.1:8084"


def test_compression_disabled_by_default(session):
    """Without ROBYN_COMPRESSION set, responses are not compressed."""
    r = requests.get(f"{BASE_URL}/sync/str/large", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert r.headers.get("Content-Encoding") is None
    assert r.text == "compress me " * 5000


def test_compression_enabled_gzips_large_responses(compression_session):
    """With ROBYN_COMPRESSION=1, a client that accepts gzip gets a compressed response."""
    r = requests.get(f"{COMPRESSION_BASE_URL}/sync/str/large", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert r.headers.get("Content-Encoding") == "gzip"
    # requests transparently decodes gzip, so the body is unaffected
    assert r.text == "compress me " * 5000


def test_compression_skipped_without_accept_encoding(compression_session):
    """A client that doesn't advertise gzip support gets an uncompressed response."""
    r = requests.get(f"{COMPRESSION_BASE_URL}/sync/str/large", headers={"Accept-Encoding": "identity"})
    assert r.status_code == 200
    assert r.headers.get("Content-Encoding") is None


def test_compression_skips_sse_streams(compression_session):
    """SSE responses opt out of compression so real-time delivery isn't buffered (#485)."""
    r = requests.get(f"{COMPRESSION_BASE_URL}/sse/basic", stream=True, headers={"Accept-Encoding": "gzip"}, timeout=5)
    assert r.status_code == 200
    assert r.headers.get("Content-Encoding") == "identity"
