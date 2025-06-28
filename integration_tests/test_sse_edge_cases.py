# Test SSE edge cases and error conditions
# Tests error handling, edge cases, and boundary conditions for SSE

import pytest
import time
import threading
from robyn import Headers, sse_response, sse_message, StreamingResponse
from integration_tests.helpers.http_methods_helpers import get, BASE_URL


class TestSSEEdgeCases:
    """Test edge cases and error conditions for SSE"""

    def test_sse_const_route_restriction(self):
        """Test that const routes don't support streaming responses"""
        # This would be tested at the route level, but we can't easily test
        # const route failures without modifying the base routes
        # This is more of a documentation test
        pass

    def test_sse_empty_generator(self):
        """Test SSE with empty generator"""
        def empty_generator():
            return
            yield  # This will never be reached
        
        response = sse_response(empty_generator())
        assert isinstance(response, StreamingResponse)

    def test_sse_generator_with_none_values(self):
        """Test SSE generator that yields None values"""
        def none_generator():
            yield "data: first\n\n"
            yield None  # This should be handled gracefully
            yield "data: second\n\n"
        
        response = sse_response(none_generator())
        assert isinstance(response, StreamingResponse)

    def test_sse_very_long_message(self):
        """Test SSE with very long messages"""
        long_message = "x" * 10000  # 10KB message
        result = sse_message(long_message)
        
        assert f"data: {long_message}" in result
        assert result.endswith("\n\n")

    def test_sse_message_with_colon_in_data(self):
        """Test sse_message with colons in the data"""
        data_with_colon = "key: value, another: value"
        result = sse_message(data_with_colon)
        
        assert f"data: {data_with_colon}" in result

    def test_sse_message_with_newlines_in_fields(self):
        """Test sse_message with newlines in event/id fields"""
        # SSE spec says fields should not contain newlines, but we should handle it
        result = sse_message("data", event="test\nevent", id="id\nwith\nnewlines")
        
        # The function should handle this gracefully
        assert "data: data" in result

    def test_sse_response_zero_status_code(self):
        """Test SSE response with zero status code"""
        def simple_generator():
            yield "data: test\n\n"
        
        # Status code 0 might be normalized to default
        response = sse_response(simple_generator(), status_code=0)
        # The response should handle this - either keep 0 or default to 200
        assert response.status_code in [0, 200]

    def test_sse_headers_modification(self):
        """Test modifying SSE headers after creation"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = sse_response(simple_generator())
        
        # Should be able to modify headers
        response.headers.set("X-Modified", "yes")
        assert response.headers.get("X-Modified") == "yes"
        
        # Original SSE headers should still be there
        assert response.headers.get("Content-Type") == "text/event-stream"

    def test_sse_unicode_and_special_chars(self):
        """Test SSE with various unicode and special characters"""
        special_chars = "🚀 Special chars: \n\t\r\"'\\áéíóú"
        result = sse_message(special_chars)
        
        # Should handle unicode properly
        assert "🚀" in result
        # Newlines should be split into multiple data lines
        lines = result.split('\n')
        data_lines = [line for line in lines if line.startswith("data:")]
        assert len(data_lines) > 1  # Should split on newlines

    def test_sse_concurrent_generator_access(self):
        """Test that SSE generators handle concurrent access properly"""
        call_count = 0
        
        def counting_generator():
            nonlocal call_count
            for i in range(3):
                call_count += 1
                yield f"data: {i}\n\n"
        
        response = sse_response(counting_generator())
        
        # The generator shouldn't be consumed during response creation
        assert call_count == 0

    def test_sse_message_numeric_values(self):
        """Test sse_message with numeric values for fields"""
        result = sse_message("test", id=123, retry=5000)
        
        assert "id: 123" in result
        assert "retry: 5000" in result

    def test_sse_response_headers_type_validation(self):
        """Test that SSE response validates headers type"""
        def simple_generator():
            yield "data: test\n\n"
        
        # Should work with Headers object
        headers = Headers({"X-Test": "value"})
        response = sse_response(simple_generator(), headers=headers)
        assert response.headers.get("X-Test") == "value"
        
        # Should work with None
        response2 = sse_response(simple_generator(), headers=None)
        assert response2.headers.get("Content-Type") == "text/event-stream"

    def test_sse_message_empty_fields(self):
        """Test sse_message with empty field values"""
        result = sse_message("data", event="", id="", retry=None)
        lines = result.split('\n')
        
        # Empty strings are falsy, so they won't appear in output
        # Only data field should appear
        assert "data: data" in lines
        # Empty event and id should NOT appear (they are falsy)
        assert not any(line.startswith("event:") for line in lines)
        assert not any(line.startswith("id:") for line in lines)
        # None retry should not appear
        assert not any(line.startswith("retry:") for line in lines)

    def test_sse_generator_exception_handling(self):
        """Test how SSE handles generator exceptions"""
        def error_generator():
            yield "data: first\n\n"
            raise ValueError("Test error")
            yield "data: second\n\n"  # This should never be reached
        
        # The response should be created successfully
        response = sse_response(error_generator())
        assert isinstance(response, StreamingResponse)
        
        # The actual error would be handled at stream consumption time

    def test_sse_async_generator_types(self):
        """Test different async generator patterns"""
        async def async_gen_with_sleep():
            import asyncio
            yield "data: start\n\n"
            await asyncio.sleep(0.001)  # Very short sleep
            yield "data: end\n\n"
        
        response = sse_response(async_gen_with_sleep())
        assert isinstance(response, StreamingResponse)

    def test_sse_message_formatting_consistency(self):
        """Test that sse_message formatting is consistent"""
        # Same message should always produce same output
        msg1 = sse_message("test", event="e", id="1")
        msg2 = sse_message("test", event="e", id="1")
        assert msg1 == msg2
        
        # Different order of parameters should produce same output
        msg3 = sse_message("test", id="1", event="e")
        assert msg1 == msg3

    def test_streaming_response_content_access(self):
        """Test accessing content from StreamingResponse"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = StreamingResponse(content=simple_generator())
        
        # Should be able to access the content generator
        assert response.content is not None
        # But we can't easily test iteration without consuming it

    def test_sse_headers_case_sensitivity(self):
        """Test SSE headers case sensitivity"""
        def simple_generator():
            yield "data: test\n\n"
        
        # Headers should be case-insensitive for retrieval
        response = sse_response(simple_generator())
        
        # These should all work (depending on Headers implementation)
        content_type = (response.headers.get("Content-Type") or 
                       response.headers.get("content-type") or
                       response.headers.get("CONTENT-TYPE"))
        assert content_type == "text/event-stream"

    def test_sse_response_immutability(self):
        """Test that SSE response properties can be modified if needed"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = sse_response(simple_generator())
        original_status = response.status_code
        
        # Should be able to modify status code
        response.status_code = 202
        assert response.status_code == 202
        assert response.status_code != original_status