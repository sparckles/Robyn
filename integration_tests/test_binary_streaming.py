import os

import pytest
import requests

from integration_tests.helpers.http_methods_helpers import BASE_URL


@pytest.mark.benchmark
def test_stream_bytes_basic(session):
    """Test that binary bytes can be streamed without error"""
    response = requests.get(f"{BASE_URL}/stream/bytes", stream=True, timeout=5)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/octet-stream"

    # Collect all streamed data
    data = b""
    for chunk in response.iter_content(chunk_size=None):
        if chunk:
            data += chunk

    # We expect 3 chunks of 1024 bytes each
    assert len(data) == 3 * 1024

    # Verify chunk contents: chunk i is filled with byte value i
    for i in range(3):
        chunk = data[i * 1024 : (i + 1) * 1024]
        assert chunk == bytes([i] * 1024), f"Chunk {i} has unexpected content"


@pytest.mark.benchmark
def test_stream_bytes_no_sse_headers(session):
    """Test that binary streaming responses do NOT include SSE-specific headers"""
    response = requests.get(f"{BASE_URL}/stream/bytes", stream=True, timeout=5)
    assert response.status_code == 200

    # SSE-specific headers should NOT be present for binary streams
    assert response.headers.get("X-Accel-Buffering") is None
    assert response.headers.get("Pragma") is None
    assert response.headers.get("Expires") is None


@pytest.mark.benchmark
def test_stream_bytes_file(session):
    """Test streaming a file in binary mode"""
    response = requests.get(f"{BASE_URL}/stream/bytes_file", stream=True, timeout=5)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/octet-stream"
    assert "attachment" in response.headers.get("Content-Disposition", "")

    # Collect all streamed data
    streamed_data = b""
    for chunk in response.iter_content(chunk_size=None):
        if chunk:
            streamed_data += chunk

    # Read the original file to compare
    test_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "build", "index.html"
    )
    with open(test_file, "rb") as f:
        original_data = f.read()

    assert streamed_data == original_data, "Streamed file content does not match original"


@pytest.mark.benchmark
def test_stream_text_still_works(session):
    """Test that string-based streaming still works after the bytes change"""
    response = requests.get(f"{BASE_URL}/stream/mixed_text", stream=True, timeout=5)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "text/plain"

    content = b""
    for chunk in response.iter_content(chunk_size=None):
        if chunk:
            content += chunk

    text = content.decode("utf-8")
    for i in range(3):
        assert f"text chunk {i}" in text
