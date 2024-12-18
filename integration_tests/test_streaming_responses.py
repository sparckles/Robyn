"""
Test module for Robyn's streaming response functionality.

This module contains tests for various streaming response scenarios including:
- Basic synchronous streaming
- Asynchronous streaming
- Mixed content type streaming (bytes, str, int, json)
- Server-Sent Events (SSE)
- Large file streaming
- CSV streaming

Each test verifies both the response headers and the streamed content.
"""

import json
import pytest
import aiohttp

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

async def test_sync_stream():
    """Test basic synchronous streaming response."""
    async with aiohttp.ClientSession() as client:
        async with client.get("http://127.0.0.1:8080/stream/sync") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "text/plain"

            chunks = []
            async for chunk in response.content:
                chunks.append(chunk.decode())

            assert len(chunks) == 5
            for i, chunk in enumerate(chunks):
                assert chunk == f"Chunk {i}\n"

async def test_async_stream():
    """Test asynchronous streaming response."""
    async with aiohttp.ClientSession() as client:
        async with client.get("http://127.0.0.1:8080/stream/async") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "text/plain"

            chunks = []
            async for chunk in response.content:
                chunks.append(chunk.decode())

            assert len(chunks) == 5
            for i, chunk in enumerate(chunks):
                assert chunk == f"Async Chunk {i}\n"

async def test_mixed_stream():
    """Test streaming of mixed content types."""
    async with aiohttp.ClientSession() as client:
        async with client.get("http://127.0.0.1:8080/stream/mixed") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "text/plain"

            expected = [
                b"Binary chunk\n",
                b"String chunk\n",
                b"42\n",
                json.dumps({"message": "JSON chunk", "number": 123}).encode() + b"\n"
            ]

            chunks = []
            async for chunk in response.content:
                chunks.append(chunk)

            assert len(chunks) == len(expected)
            for chunk, expected_chunk in zip(chunks, expected):
                assert chunk == expected_chunk

async def test_server_sent_events():
    """Test Server-Sent Events (SSE) streaming."""
    async with aiohttp.ClientSession() as client:
        async with client.get("http://127.0.0.1:8080/stream/events") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "text/event-stream"
            assert response.headers["Cache-Control"] == "no-cache"
            assert response.headers["Connection"] == "keep-alive"

            events = []
            async for chunk in response.content:
                events.append(chunk.decode())

            # Test first event (message)
            assert "event: message\n" in events[0]
            assert "data: {" in events[0]
            event_data = json.loads(events[0].split("data: ")[1].strip())
            assert "time" in event_data
            assert event_data["type"] == "start"

            # Test second event (with ID)
            assert "id: 1\n" in events[1]
            assert "event: update\n" in events[1]
            event_data = json.loads(events[1].split("data: ")[1].strip())
            assert event_data["progress"] == 50

            # Test third event (complete)
            assert "event: complete\n" in events[2]
            event_data = json.loads(events[2].split("data: ")[1].strip())
            assert event_data["status"] == "complete"
            assert event_data["results"] == [1, 2, 3]

async def test_large_file_stream():
    """Test streaming of large files in chunks."""
    async with aiohttp.ClientSession() as client:
        async with client.get("http://127.0.0.1:8080/stream/large-file") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "application/octet-stream"
            assert response.headers["Content-Disposition"] == "attachment; filename=large-file.bin"

            total_size = 0
            async for chunk in response.content:
                assert len(chunk) <= 1024  # Max chunk size
                total_size += len(chunk)

            assert total_size == 10 * 1024  # 10KB total

async def test_csv_stream():
    """Test streaming of CSV data."""
    async with aiohttp.ClientSession() as client:
        async with client.get("http://127.0.0.1:8080/stream/csv") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "text/csv"
            assert response.headers["Content-Disposition"] == "attachment; filename=data.csv"

            lines = []
            async for chunk in response.content:
                lines.extend(chunk.decode().splitlines())

            # Verify header
            assert lines[0] == "id,name,value"
            
            # Verify data rows
            assert len(lines) == 6  # Header + 5 data rows
            for i, line in enumerate(lines[1:], 0):
                id_, name, value = line.split(',')
                assert int(id_) == i
                assert name == f"item-{i}"
                assert 1 <= int(value) <= 100