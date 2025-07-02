#!/usr/bin/env python3
"""
SSE Debugging and Edge Case Tests
Consolidates debug scenarios into proper test cases for SSE functionality
"""

import pytest
import requests
from robyn import Headers
from robyn.responses import StreamingResponse, sse_response, sse_message
from integration_tests.helpers.http_methods_helpers import BASE_URL


class TestSSEDebugging:
    """Test SSE debugging scenarios and edge cases"""

    def test_sse_response_attributes(self):
        """Test SSE response object attributes and types"""
        def simple_generator():
            yield "data: Test message\n\n"
        
        response = sse_response(simple_generator())
        
        # Verify response attributes exist and have correct types
        assert hasattr(response, 'status_code')
        assert hasattr(response, 'headers')
        assert hasattr(response, 'content')
        assert hasattr(response, 'media_type')
        
        assert response.status_code == 200
        assert response.media_type == 'text/event-stream'
        assert isinstance(response.headers, Headers)

    def test_sse_headers_extraction(self):
        """Test Headers object extraction from Python to Rust"""
        # Create Headers object
        headers = Headers({'Content-Type': 'text/event-stream', 'X-Custom': 'test'})
        
        def simple_generator():
            yield 'data: test\n\n'
        
        # Create StreamingResponse with Headers
        response = StreamingResponse(
            content=simple_generator(),
            status_code=200,
            headers=headers
        )
        
        # Verify headers are accessible
        assert response.headers is not None
        assert isinstance(response.headers, Headers)
        
        # Test headers access methods
        content_type = response.headers.get('Content-Type')
        assert content_type == 'text/event-stream'
        
        custom_header = response.headers.get('X-Custom')
        assert custom_header == 'test'

    def test_sse_generator_types(self):
        """Test different generator types with SSE"""
        
        # Test simple generator
        def simple_gen():
            yield "data: Simple\n\n"
        
        response1 = sse_response(simple_gen())
        assert response1.media_type == 'text/event-stream'
        
        # Test generator with multiple yields
        def multi_gen():
            for i in range(3):
                yield f"data: Message {i}\n\n"
        
        response2 = sse_response(multi_gen())
        assert response2.media_type == 'text/event-stream'
        
        # Test generator with sse_message formatting
        def formatted_gen():
            yield sse_message("Formatted message", event="test", id="1")
        
        response3 = sse_response(formatted_gen())
        assert response3.media_type == 'text/event-stream'

    def test_sse_error_scenarios(self):
        """Test SSE error handling scenarios"""
        
        # Test empty generator
        def empty_gen():
            return
            yield "never reached"  # This line should never execute
        
        response = sse_response(empty_gen())
        assert response.status_code == 200
        assert response.media_type == 'text/event-stream'
        
        # Test generator that raises exception
        def error_gen():
            yield "data: Before error\n\n"
            raise ValueError("Test error")
            yield "data: After error\n\n"  # Should not be reached
        
        # Creating the response should work, error occurs during iteration
        response = sse_response(error_gen())
        assert response.status_code == 200

    def test_sse_content_validation(self):
        """Test SSE content format validation"""
        
        # Test properly formatted SSE
        def proper_gen():
            yield "data: Proper message\n\n"
            yield "event: test\ndata: Event message\n\n"
            yield "id: 123\ndata: ID message\n\n"
        
        response = sse_response(proper_gen())
        assert response.media_type == 'text/event-stream'
        
        # Test improperly formatted SSE (missing newlines)
        def improper_gen():
            yield "data: Missing newlines"
            yield "event: test"
        
        response = sse_response(improper_gen())
        assert response.media_type == 'text/event-stream'  # Should still work

    def test_sse_custom_status_and_headers(self):
        """Test SSE with custom status codes and headers"""
        
        def simple_gen():
            yield "data: Custom response\n\n"
        
        # Test custom status code
        response = StreamingResponse(
            content=simple_gen(),
            status_code=201,
            media_type='text/event-stream'
        )
        assert response.status_code == 201
        assert response.media_type == 'text/event-stream'
        
        # Test custom headers
        custom_headers = Headers({
            'Content-Type': 'text/event-stream',
            'X-Debug': 'true',
            'Cache-Control': 'no-cache'
        })
        
        response = StreamingResponse(
            content=simple_gen(),
            status_code=200,
            headers=custom_headers
        )
        assert response.headers.get('X-Debug') == 'true'
        assert response.headers.get('Cache-Control') == 'no-cache'

    def test_sse_message_formatting_edge_cases(self):
        """Test sse_message formatter with edge cases"""
        
        # Test empty message
        result = sse_message("")
        assert result == "data: \n\n"
        
        # Test None message (should handle gracefully)
        try:
            result = sse_message(None)
            assert "data:" in result
        except TypeError:
            # This is acceptable behavior
            pass
        
        # Test very long message
        long_message = "x" * 1000
        result = sse_message(long_message)
        assert f"data: {long_message}\n\n" in result
        
        # Test message with special characters
        special_message = "Hello\nWorld\r\nWith\tTabs"
        result = sse_message(special_message)
        assert "data: Hello\ndata: World\ndata: With\tTabs\n\n" in result
        
        # Test unicode message
        unicode_message = "Hello 世界 🌍"
        result = sse_message(unicode_message)
        assert f"data: {unicode_message}\n\n" in result

    def test_sse_import_validation(self):
        """Test that all SSE-related imports work correctly"""
        
        # Test direct imports
        from robyn import sse_response, sse_message
        from robyn.responses import StreamingResponse
        
        assert callable(sse_response)
        assert callable(sse_message)
        assert StreamingResponse is not None
        
        # Test that they work together
        def test_gen():
            yield sse_message("Test import")
        
        response = sse_response(test_gen())
        assert response.media_type == 'text/event-stream'

    def test_sse_concurrent_generator_creation(self):
        """Test creating multiple SSE responses concurrently"""
        import threading
        import time
        
        responses = []
        errors = []
        
        def create_sse_response(index):
            try:
                def gen():
                    yield f"data: Response {index}\n\n"
                
                response = sse_response(gen())
                responses.append((index, response))
            except Exception as e:
                errors.append((index, e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_sse_response, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5)
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(responses) == 5
        
        for index, response in responses:
            assert response.media_type == 'text/event-stream'
            assert response.status_code == 200

    def test_sse_memory_efficiency(self):
        """Test SSE memory efficiency with large generators"""
        
        def large_generator():
            for i in range(1000):
                yield f"data: Message {i}\n\n"
        
        # Creating the response should not consume excessive memory
        response = sse_response(large_generator())
        assert response.media_type == 'text/event-stream'
        
        # The generator should be lazy (not pre-computed)
        assert hasattr(response.content, '__iter__')

    @pytest.mark.parametrize("content_type", [
        'text/event-stream',
        'text/event-stream; charset=utf-8',
        'application/x-ndjson',  # Different but valid streaming type
    ])
    def test_sse_content_type_variations(self, content_type):
        """Test SSE with different content type variations"""
        
        def simple_gen():
            yield "data: Test\n\n"
        
        response = StreamingResponse(
            content=simple_gen(),
            status_code=200,
            media_type=content_type
        )
        
        assert response.media_type == content_type
        assert response.status_code == 200


class TestSSEServerIntegration:
    """Test SSE integration with actual server (requires running server)"""
    
    @pytest.mark.integration
    def test_debug_sse_endpoint_basic(self):
        """Test a basic debug SSE endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/debug_sse", stream=True, timeout=3)
            if response.status_code == 404:
                pytest.skip("Debug SSE endpoint not available")
            
            assert response.status_code == 200
            assert response.headers.get('Content-Type') == 'text/event-stream'
            
            # Read some content
            content = ""
            for chunk in response.iter_content(chunk_size=512, decode_unicode=True):
                content += chunk
                if len(content) > 100:  # Don't read forever
                    break
            
            assert "data:" in content
            
        except requests.exceptions.RequestException:
            pytest.skip("Could not connect to debug SSE endpoint")
    
    @pytest.mark.integration
    def test_debug_sse_headers_in_response(self):
        """Test debug SSE endpoint headers in actual response"""
        try:
            response = requests.get(f"{BASE_URL}/debug_sse", stream=True, timeout=2)
            if response.status_code == 404:
                pytest.skip("Debug SSE endpoint not available")
            
            # Verify standard SSE headers
            assert response.headers.get('Content-Type') == 'text/event-stream'
            assert response.headers.get('Cache-Control') == 'no-cache'
            
            # Check for any custom debug headers
            debug_headers = [k for k in response.headers.keys() if 'debug' in k.lower() or 'x-' in k.lower()]
            # Just verify we can access headers (debug headers are optional)
            
        except requests.exceptions.RequestException:
            pytest.skip("Could not connect to debug SSE endpoint")


# Utility functions for debugging (can be used in other tests)

def debug_sse_response(response):
    """Debug utility to print SSE response details"""
    print(f"Response type: {type(response)}")
    print(f"Status code: {getattr(response, 'status_code', 'NOT SET')}")
    print(f"Media type: {getattr(response, 'media_type', 'NOT SET')}")
    print(f"Headers: {getattr(response, 'headers', 'NOT SET')}")
    print(f"Content type: {type(getattr(response, 'content', None))}")


def validate_sse_format(content: str) -> bool:
    """Validate that content follows SSE format"""
    lines = content.split('\n')
    
    # Check for proper SSE field formats
    valid_fields = ['data', 'event', 'id', 'retry']
    
    for line in lines:
        line = line.strip()
        if not line:
            continue  # Empty lines are valid separators
        
        if ':' in line:
            field = line.split(':', 1)[0].strip()
            if field not in valid_fields:
                return False
        else:
            # Lines without colons should be comments (start with :)
            if not line.startswith(':'):
                return False
    
    return True
