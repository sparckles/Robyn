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
from robyn import Robyn
from robyn.robyn import Request
from integration_tests.base_routes import app


@pytest.mark.asyncio
async def test_sync_stream():
    """Test basic synchronous streaming response.
    
    Verifies that:
    1. Response has correct content type
    2. Chunks are received in correct order
    3. Each chunk has expected format
    """
    async with app.test_client() as client:
        response = await client.get("/stream/sync")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/plain"

        chunks = []
        async for chunk in response.content:
            chunks.append(chunk.decode())

        assert len(chunks) == 5
        for i, chunk in enumerate(chunks):
            assert chunk == f"Chunk {i}\n"


@pytest.mark.asyncio
async def test_async_stream():
    """Test asynchronous streaming response.
    
    Verifies that:
    1. Response has correct content type
    2. Chunks are received in correct order with delays
    3. Each chunk has expected format
    """
    async with app.test_client() as client:
        response = await client.get("/stream/async")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/plain"

        chunks = []
        async for chunk in response.content:
            chunks.append(chunk.decode())

        assert len(chunks) == 5
        for i, chunk in enumerate(chunks):
            assert chunk == f"Async Chunk {i}\n"


@pytest.mark.asyncio
async def test_mixed_stream():
    """Test streaming of mixed content types.
    
    Verifies that:
    1. Response handles different content types:
       - Binary data
       - String data
       - Integer data
       - JSON data
    2. Each chunk is correctly encoded
    """
    async with app.test_client() as client:
        response = await client.get("/stream/mixed")
        assert response.status_code == 200
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


@pytest.mark.asyncio
async def test_server_sent_events():
    """Test Server-Sent Events (SSE) streaming.
    
    Verifies that:
    1. Response has correct SSE headers
    2. Events are properly formatted with:
       - Event type
       - Event ID (when provided)
       - Event data
    """
    async with app.test_client() as client:
        response = await client.get("/stream/events")
        assert response.status_code == 200
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


@pytest.mark.asyncio
async def test_large_file_stream():
    """Test streaming of large files in chunks.
    
    Verifies that:
    1. Response has correct headers for file download
    2. Content is streamed in correct chunk sizes
    3. Total content length matches expected size
    """
    async with app.test_client() as client:
        response = await client.get("/stream/large-file")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/octet-stream"
        assert response.headers["Content-Disposition"] == "attachment; filename=large-file.bin"

        total_size = 0
        async for chunk in response.content:
            assert len(chunk) <= 1024  # Max chunk size
            total_size += len(chunk)

        assert total_size == 10 * 1024  # 10KB total


@pytest.mark.asyncio
async def test_csv_stream():
    """Test streaming of CSV data.
    
    Verifies that:
    1. Response has correct CSV headers
    2. CSV content is properly formatted
    3. All rows are received in correct order
    """
    async with app.test_client() as client:
        response = await client.get("/stream/csv")
        assert response.status_code == 200
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