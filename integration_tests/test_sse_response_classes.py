# Test SSE response classes and utilities
# Tests the Python API for creating SSE responses

import pytest
from robyn import Headers, sse_response, sse_message, StreamingResponse


class TestSSEResponseClasses:
    """Test SSE response classes and utility functions"""

    def test_sse_message_basic(self):
        """Test basic sse_message formatting"""
        result = sse_message("Hello world")
        expected = "data: Hello world\n\n"
        assert result == expected

    def test_sse_message_with_event(self):
        """Test sse_message with event type"""
        result = sse_message("Hello", event="greeting")
        lines = result.split('\n')
        assert "event: greeting" in lines
        assert "data: Hello" in lines
        assert lines[-1] == ""  # Should end with empty line
        assert lines[-2] == ""  # Double newline

    def test_sse_message_with_id(self):
        """Test sse_message with ID"""
        result = sse_message("Hello", id="123")
        lines = result.split('\n')
        assert "id: 123" in lines
        assert "data: Hello" in lines

    def test_sse_message_with_retry(self):
        """Test sse_message with retry time"""
        result = sse_message("Hello", retry=5000)
        lines = result.split('\n')
        assert "retry: 5000" in lines
        assert "data: Hello" in lines

    def test_sse_message_all_fields(self):
        """Test sse_message with all fields"""
        result = sse_message("Test message", event="test", id="456", retry=3000)
        lines = result.split('\n')
        assert "event: test" in lines
        assert "id: 456" in lines
        assert "retry: 3000" in lines
        assert "data: Test message" in lines
        assert result.endswith("\n\n")

    def test_sse_message_multiline_data(self):
        """Test sse_message with multiline data"""
        result = sse_message("Line 1\nLine 2\nLine 3")
        lines = result.split('\n')
        assert "data: Line 1" in lines
        assert "data: Line 2" in lines
        assert "data: Line 3" in lines

    def test_sse_message_empty_data(self):
        """Test sse_message with empty data"""
        result = sse_message("")
        expected = "data: \n\n"
        assert result == expected

    def test_streaming_response_creation(self):
        """Test StreamingResponse creation"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = StreamingResponse(
            content=simple_generator(),
            status_code=200,
            headers=Headers({"X-Test": "value"}),
            media_type="text/event-stream"
        )
        
        assert response.status_code == 200
        assert response.media_type == "text/event-stream"
        assert response.headers.get("X-Test") == "value"
        # Check default SSE headers
        assert response.headers.get("Content-Type") == "text/event-stream"
        assert response.headers.get("Cache-Control") == "no-cache"
        assert response.headers.get("Connection") == "keep-alive"

    def test_streaming_response_default_headers(self):
        """Test that StreamingResponse sets correct default headers for SSE"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = StreamingResponse(content=simple_generator())
        
        # Check that default SSE headers are set
        assert response.headers.get("Content-Type") == "text/event-stream"
        assert response.headers.get("Cache-Control") == "no-cache"
        assert response.headers.get("Connection") == "keep-alive"
        assert response.headers.get("Access-Control-Allow-Origin") == "*"

    def test_sse_response_function(self):
        """Test sse_response convenience function"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = sse_response(simple_generator())
        
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "text/event-stream"
        assert response.status_code == 200

    def test_sse_response_with_custom_status(self):
        """Test sse_response with custom status code"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = sse_response(simple_generator(), status_code=201)
        
        assert response.status_code == 201
        assert response.media_type == "text/event-stream"

    def test_sse_response_with_custom_headers(self):
        """Test sse_response with custom headers"""
        def simple_generator():
            yield "data: test\n\n"
        
        custom_headers = Headers({"X-Custom": "value"})
        response = sse_response(simple_generator(), headers=custom_headers)
        
        assert response.headers.get("X-Custom") == "value"
        # Should still have default SSE headers
        assert response.headers.get("Content-Type") == "text/event-stream"

    def test_generator_function_types(self):
        """Test that different generator types work"""
        # Regular generator function
        def sync_generator():
            for i in range(3):
                yield f"data: {i}\n\n"
        
        # Async generator function
        async def async_generator():
            for i in range(3):
                yield f"data: {i}\n\n"
        
        # Test with sync generator
        response1 = sse_response(sync_generator())
        assert isinstance(response1, StreamingResponse)
        
        # Test with async generator
        response2 = sse_response(async_generator())
        assert isinstance(response2, StreamingResponse)

    def test_sse_message_field_order(self):
        """Test that SSE message fields are in correct order"""
        result = sse_message("data", event="test", id="123", retry=1000)
        lines = result.split('\n')
        
        # Find the positions of each field
        event_pos = next(i for i, line in enumerate(lines) if line.startswith("event:"))
        id_pos = next(i for i, line in enumerate(lines) if line.startswith("id:"))
        retry_pos = next(i for i, line in enumerate(lines) if line.startswith("retry:"))
        data_pos = next(i for i, line in enumerate(lines) if line.startswith("data:"))
        
        # Order should be: event, id, retry, data
        assert event_pos < id_pos < retry_pos < data_pos

    def test_sse_message_special_characters(self):
        """Test sse_message with special characters"""
        # Test with newlines, unicode, etc.
        result = sse_message("Hello 🌍\nWorld 💫", event="unicode")
        lines = result.split('\n')
        assert "event: unicode" in lines
        assert "data: Hello 🌍" in lines
        assert "data: World 💫" in lines

    def test_streaming_response_non_sse_media_type(self):
        """Test StreamingResponse with non-SSE media type"""
        def simple_generator():
            yield "chunk1"
        
        response = StreamingResponse(
            content=simple_generator(),
            media_type="text/plain"
        )
        
        # Should not set SSE headers for non-SSE media types
        assert response.media_type == "text/plain"
        assert response.headers.get("Content-Type") != "text/event-stream"

    def test_headers_class_integration(self):
        """Test integration with Robyn Headers class"""
        headers = Headers({
            "X-Custom-1": "value1",
            "X-Custom-2": "value2"
        })
        
        def simple_generator():
            yield "data: test\n\n"
        
        response = sse_response(simple_generator(), headers=headers)
        
        assert response.headers.get("X-Custom-1") == "value1"
        assert response.headers.get("X-Custom-2") == "value2"
        # Should still have SSE headers
        assert response.headers.get("Content-Type") == "text/event-stream"