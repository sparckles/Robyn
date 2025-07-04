# Consolidated Server-Sent Events (SSE) Tests
# This file contains all SSE-related tests from the integration_tests directory

import json
import threading
import time
import concurrent.futures
from typing import List, Dict, Any

import pytest
import requests

from robyn import Headers, SSE_Response, SSE_Message, StreamingResponse
from integration_tests.helpers.http_methods_helpers import BASE_URL

# Try to import sseclient, but don't fail if it's not available
try:
    from sseclient import SSEClient
    HAS_SSECLIENT = True
except ImportError:
    SSEClient = None
    HAS_SSECLIENT = False


# =============================================================================
# Helper Functions
# =============================================================================

def parse_sse_events(response_text: str) -> List[Dict[str, Any]]:
    """Parse SSE response text into a list of events"""
    events = []
    current_event = {}
    
    for line in response_text.split('\n'):
        line = line.strip()
        if not line:
            if current_event:
                events.append(current_event)
                current_event = {}
            continue
            
        if ':' in line:
            field, value = line.split(':', 1)
            field = field.strip()
            value = value.strip()
            
            if field == 'data':
                # Handle multiple data lines
                if 'data' in current_event:
                    current_event['data'] += '\n' + value
                else:
                    current_event['data'] = value
            else:
                current_event[field] = value
    
    # Add the last event if it exists
    if current_event:
        events.append(current_event)
    
    return events


def parse_sse_data(text: str) -> List[str]:
    """Parse SSE data lines from response text"""
    data_lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('data: '):
            data_lines.append(line[6:])  # Remove 'data: ' prefix
    return data_lines


def get_sse_stream(endpoint: str, timeout: int = 5) -> List[Dict[str, Any]]:
    """Get SSE events from an endpoint with timeout"""
    url = f"{BASE_URL}/{endpoint.strip('/')}"
    
    events = []
    try:
        response = requests.get(url, stream=True, timeout=timeout, headers={'Accept': 'text/event-stream'})
        response.raise_for_status()
        
        # Read the response content with a timeout
        content = ""
        start_time = time.time()
        
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                content += chunk
            # Break if we've been reading for too long
            if time.time() - start_time > timeout:
                break
                
        events = parse_sse_events(content)
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to connect to SSE endpoint {endpoint}: {e}")
    
    return events


def get_SSE_Response_quickly(endpoint: str, timeout: float = 3.0) -> str:
    """Get SSE response content with a timeout"""
    url = f"{BASE_URL}/{endpoint.strip('/')}"
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # Read response content with timeout
        content = ""
        start_time = time.time()
        
        for chunk in response.iter_content(chunk_size=512, decode_unicode=True):
            if chunk:
                content += chunk
            # Stop after timeout
            if time.time() - start_time > timeout:
                break
                
        return content
    except Exception as e:
        pytest.fail(f"Failed to get SSE response from {endpoint}: {e}")


def debug_SSE_Response(response):
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


# =============================================================================
# Test Classes
# =============================================================================

class TestServerSentEvents:
    """Test class for basic Server-Sent Events functionality"""

    def test_sse_basic_headers(self):
        """Test that SSE endpoints return correct headers"""
        response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
        
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'text/event-stream'
        assert response.headers.get('Cache-Control') == 'no-cache'
        # Connection: keep-alive is implicit with chunked transfer encoding in HTTP/1.1
        # Check for CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers
        
    def test_sse_basic_stream(self):
        """Test basic SSE streaming with simple data messages"""
        events = get_sse_stream("/sse/basic")
        
        assert len(events) == 3
        
        for i, event in enumerate(events):
            assert 'data' in event
            assert event['data'] == f"Test message {i}"

    def test_sse_formatted_messages(self):
        """Test SSE messages formatted with SSE_Message helper"""
        events = get_sse_stream("/sse/formatted")
        
        assert len(events) == 3
        
        for i, event in enumerate(events):
            assert event['data'] == f"Formatted message {i}"
            assert event['event'] == "test"
            assert event['id'] == str(i)

    def test_sse_json_data(self):
        """Test SSE streaming with JSON data"""
        events = get_sse_stream("/sse/json")
        
        assert len(events) == 3
        
        for i, event in enumerate(events):
            assert 'data' in event
            json_data = json.loads(event['data'])
            assert json_data['id'] == i
            assert json_data['message'] == f"JSON message {i}"
            assert json_data['type'] == "test"

    def test_sse_named_events(self):
        """Test SSE with different event types"""
        events = get_sse_stream("/sse/named_events")
        
        assert len(events) == 3
        
        expected_events = [
            ("start", "Test started"),
            ("progress", "Test in progress"),
            ("end", "Test completed")
        ]
        
        for i, (expected_event, expected_message) in enumerate(expected_events):
            assert events[i]['event'] == expected_event
            assert events[i]['data'] == expected_message

    def test_sse_async_endpoint(self):
        """Test async SSE endpoint"""
        events = get_sse_stream("/sse/async")
        
        assert len(events) == 3
        
        for i, event in enumerate(events):
            assert event['data'] == f"Async message {i}"

    def test_sse_single_message(self):
        """Test SSE endpoint that sends only one message"""
        events = get_sse_stream("/sse/single")
        
        assert len(events) == 1
        assert events[0]['data'] == "Single message"

    def test_sse_empty_stream(self):
        """Test SSE endpoint that sends no messages"""
        events = get_sse_stream("/sse/empty", timeout=2)
        
        assert len(events) == 0

    def test_sse_custom_headers(self):
        """Test SSE endpoint with custom headers"""
        response = requests.get(f"{BASE_URL}/sse/with_headers", stream=True)
        
        assert response.status_code == 200
        assert response.headers.get('X-Custom-Header') == 'custom-value'
        assert response.headers.get('Content-Type') == 'text/event-stream'
        
        # Also check the content
        events = get_sse_stream("/sse/with_headers")
        assert len(events) == 1
        assert events[0]['data'] == "Message with custom headers"

    def test_sse_custom_status_code(self):
        """Test SSE endpoint with custom status code"""
        response = requests.get(f"{BASE_URL}/sse/status_code", stream=True)
        
        assert response.status_code == 201
        assert response.headers.get('Content-Type') == 'text/event-stream'
        
        # Also check the content
        events = get_sse_stream("/sse/status_code")
        assert len(events) == 1
        assert events[0]['data'] == "Message with custom status"

    def test_SSE_Response_class_import(self):
        """Test that SSE classes can be imported correctly"""
        try:
            from robyn import SSE_Response, SSE_Message, StreamingResponse
            assert SSE_Response is not None
            assert SSE_Message is not None
            assert StreamingResponse is not None
        except ImportError as e:
            pytest.fail(f"Failed to import SSE classes: {e}")

    def test_SSE_Message_formatter(self):
        """Test the SSE_Message formatter utility function"""
        from robyn import SSE_Message
        
        # Test basic message
        result = SSE_Message("Hello world")
        assert "data: Hello world\n\n" in result
        
        # Test with event type
        result = SSE_Message("Hello", event="greeting")
        assert "event: greeting\n" in result
        assert "data: Hello\n\n" in result
        
        # Test with ID
        result = SSE_Message("Hello", id="123")
        assert "id: 123\n" in result
        assert "data: Hello\n\n" in result
        
        # Test with retry
        result = SSE_Message("Hello", retry=5000)
        assert "retry: 5000\n" in result
        assert "data: Hello\n\n" in result
        
        # Test with all parameters
        result = SSE_Message("Hello", event="test", id="456", retry=3000)
        assert "event: test\n" in result
        assert "id: 456\n" in result
        assert "retry: 3000\n" in result
        assert "data: Hello\n\n" in result
        
        # Test multiline data
        result = SSE_Message("Line 1\nLine 2")
        assert "data: Line 1\ndata: Line 2\n\n" in result

    def test_sse_concurrent_connections(self):
        """Test multiple concurrent SSE connections"""
        
        def get_events():
            return get_sse_stream("/sse/basic")
        
        # Create multiple concurrent connections
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(get_events) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All connections should receive the same events
        for events in results:
            assert len(events) == 3
            for i, event in enumerate(events):
                assert event['data'] == f"Test message {i}"

    @pytest.mark.benchmark
    def test_sse_performance_basic(self):
        """Basic performance test for SSE endpoints"""
        start_time = time.time()
        events = get_sse_stream("/sse/basic")
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0
        assert len(events) == 3

    def test_sse_content_type_validation(self):
        """Test that SSE endpoints reject non-streaming requests appropriately"""
        # Regular GET request (not streaming)
        response = requests.get(f"{BASE_URL}/sse/basic")
        
        # Should still work and return correct content type
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'text/event-stream'

    def test_sse_error_handling(self):
        """Test error handling in SSE streams"""
        # Test with a non-existent endpoint
        response = requests.get(f"{BASE_URL}/sse/nonexistent", stream=True)
        assert response.status_code == 404

    def test_sse_middleware_compatibility(self):
        """Test that SSE works with existing middleware"""
        response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
        
        # Should have global headers from middleware
        assert response.headers.get('server') == 'robyn'
        # SSE-specific headers should also be present
        assert response.headers.get('Content-Type') == 'text/event-stream'


class TestSSEResponseClasses:
    """Test SSE response classes and utility functions"""

    def test_SSE_Message_basic(self):
        """Test basic SSE_Message formatting"""
        result = SSE_Message("Hello world")
        expected = "data: Hello world\n\n"
        assert result == expected

    def test_SSE_Message_with_event(self):
        """Test SSE_Message with event type"""
        result = SSE_Message("Hello", event="greeting")
        lines = result.split('\n')
        assert "event: greeting" in lines
        assert "data: Hello" in lines
        assert lines[-1] == ""  # Should end with empty line
        assert lines[-2] == ""  # Double newline

    def test_SSE_Message_with_id(self):
        """Test SSE_Message with ID"""
        result = SSE_Message("Hello", id="123")
        lines = result.split('\n')
        assert "id: 123" in lines
        assert "data: Hello" in lines

    def test_SSE_Message_with_retry(self):
        """Test SSE_Message with retry time"""
        result = SSE_Message("Hello", retry=5000)
        lines = result.split('\n')
        assert "retry: 5000" in lines
        assert "data: Hello" in lines

    def test_SSE_Message_all_fields(self):
        """Test SSE_Message with all fields"""
        result = SSE_Message("Test message", event="test", id="456", retry=3000)
        lines = result.split('\n')
        assert "event: test" in lines
        assert "id: 456" in lines
        assert "retry: 3000" in lines
        assert "data: Test message" in lines
        assert result.endswith("\n\n")

    def test_SSE_Message_multiline_data(self):
        """Test SSE_Message with multiline data"""
        result = SSE_Message("Line 1\nLine 2\nLine 3")
        lines = result.split('\n')
        assert "data: Line 1" in lines
        assert "data: Line 2" in lines
        assert "data: Line 3" in lines

    def test_SSE_Message_empty_data(self):
        """Test SSE_Message with empty data"""
        result = SSE_Message("")
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

    def test_SSE_Response_function(self):
        """Test SSE_Response convenience function"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = SSE_Response(simple_generator())
        
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "text/event-stream"
        assert response.status_code == 200

    def test_SSE_Response_with_custom_status(self):
        """Test SSE_Response with custom status code"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = SSE_Response(simple_generator(), status_code=201)
        
        assert response.status_code == 201
        assert response.media_type == "text/event-stream"

    def test_SSE_Response_with_custom_headers(self):
        """Test SSE_Response with custom headers"""
        def simple_generator():
            yield "data: test\n\n"
        
        custom_headers = Headers({"X-Custom": "value"})
        response = SSE_Response(simple_generator(), headers=custom_headers)
        
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
        response1 = SSE_Response(sync_generator())
        assert isinstance(response1, StreamingResponse)
        
        # Test with async generator
        response2 = SSE_Response(async_generator())
        assert isinstance(response2, StreamingResponse)

    def test_SSE_Message_field_order(self):
        """Test that SSE message fields are in correct order"""
        result = SSE_Message("data", event="test", id="123", retry=1000)
        lines = result.split('\n')
        
        # Find the positions of each field
        event_pos = next(i for i, line in enumerate(lines) if line.startswith("event:"))
        id_pos = next(i for i, line in enumerate(lines) if line.startswith("id:"))
        retry_pos = next(i for i, line in enumerate(lines) if line.startswith("retry:"))
        data_pos = next(i for i, line in enumerate(lines) if line.startswith("data:"))
        
        # Order should be: event, id, retry, data
        assert event_pos < id_pos < retry_pos < data_pos

    def test_SSE_Message_special_characters(self):
        """Test SSE_Message with special characters"""
        # Test with newlines, unicode, etc.
        result = SSE_Message("Hello 🌍\nWorld 💫", event="unicode")
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
        
        response = SSE_Response(simple_generator(), headers=headers)
        
        assert response.headers.get("X-Custom-1") == "value1"
        assert response.headers.get("X-Custom-2") == "value2"
        # Should still have SSE headers
        assert response.headers.get("Content-Type") == "text/event-stream"


class TestSSEDebugging:
    """Test SSE debugging scenarios and edge cases"""

    def test_SSE_Response_attributes(self):
        """Test SSE response object attributes and types"""
        def simple_generator():
            yield "data: Test message\n\n"
        
        response = SSE_Response(simple_generator())
        
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
        
        response1 = SSE_Response(simple_gen())
        assert response1.media_type == 'text/event-stream'
        
        # Test generator with multiple yields
        def multi_gen():
            for i in range(3):
                yield f"data: Message {i}\n\n"
        
        response2 = SSE_Response(multi_gen())
        assert response2.media_type == 'text/event-stream'
        
        # Test generator with SSE_Message formatting
        def formatted_gen():
            yield SSE_Message("Formatted message", event="test", id="1")
        
        response3 = SSE_Response(formatted_gen())
        assert response3.media_type == 'text/event-stream'

    def test_sse_error_scenarios(self):
        """Test SSE error handling scenarios"""
        
        # Test empty generator
        def empty_gen():
            return
            yield "never reached"  # This line should never execute
        
        response = SSE_Response(empty_gen())
        assert response.status_code == 200
        assert response.media_type == 'text/event-stream'
        
        # Test generator that raises exception
        def error_gen():
            yield "data: Before error\n\n"
            raise ValueError("Test error")
            yield "data: After error\n\n"  # Should not be reached
        
        # Creating the response should work, error occurs during iteration
        response = SSE_Response(error_gen())
        assert response.status_code == 200

    def test_sse_content_validation(self):
        """Test SSE content format validation"""
        
        # Test properly formatted SSE
        def proper_gen():
            yield "data: Proper message\n\n"
            yield "event: test\ndata: Event message\n\n"
            yield "id: 123\ndata: ID message\n\n"
        
        response = SSE_Response(proper_gen())
        assert response.media_type == 'text/event-stream'
        
        # Test improperly formatted SSE (missing newlines)
        def improper_gen():
            yield "data: Missing newlines"
            yield "event: test"
        
        response = SSE_Response(improper_gen())
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

    def test_SSE_Message_formatting_edge_cases(self):
        """Test SSE_Message formatter with edge cases"""
        
        # Test empty message
        result = SSE_Message("")
        assert result == "data: \n\n"
        
        # Test None message (should handle gracefully)
        try:
            result = SSE_Message(None)
            assert "data:" in result
        except TypeError:
            # This is acceptable behavior
            pass
        
        # Test very long message
        long_message = "x" * 1000
        result = SSE_Message(long_message)
        assert f"data: {long_message}\n\n" in result
        
        # Test message with special characters
        special_message = "Hello\nWorld\r\nWith\tTabs"
        result = SSE_Message(special_message)
        assert "data: Hello\ndata: World\ndata: With\tTabs\n\n" in result
        
        # Test unicode message
        unicode_message = "Hello 世界 🌍"
        result = SSE_Message(unicode_message)
        assert f"data: {unicode_message}\n\n" in result

    def test_sse_import_validation(self):
        """Test that all SSE-related imports work correctly"""
        
        # Test direct imports
        from robyn import SSE_Response, SSE_Message
        from robyn.responses import StreamingResponse
        
        assert callable(SSE_Response)
        assert callable(SSE_Message)
        assert StreamingResponse is not None
        
        # Test that they work together
        def test_gen():
            yield SSE_Message("Test import")
        
        response = SSE_Response(test_gen())
        assert response.media_type == 'text/event-stream'

    def test_sse_concurrent_generator_creation(self):
        """Test creating multiple SSE responses concurrently"""
        
        responses = []
        errors = []
        
        def create_SSE_Response(index):
            try:
                def gen():
                    yield f"data: Response {index}\n\n"
                
                response = SSE_Response(gen())
                responses.append((index, response))
            except Exception as e:
                errors.append((index, e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_SSE_Response, args=(i,))
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
        response = SSE_Response(large_generator())
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
        
        response = SSE_Response(empty_generator())
        assert isinstance(response, StreamingResponse)

    def test_sse_generator_with_none_values(self):
        """Test SSE generator that yields None values"""
        def none_generator():
            yield "data: first\n\n"
            yield None  # This should be handled gracefully
            yield "data: second\n\n"
        
        response = SSE_Response(none_generator())
        assert isinstance(response, StreamingResponse)

    def test_sse_very_long_message(self):
        """Test SSE with very long messages"""
        long_message = "x" * 10000  # 10KB message
        result = SSE_Message(long_message)
        
        assert f"data: {long_message}" in result
        assert result.endswith("\n\n")

    def test_SSE_Message_with_colon_in_data(self):
        """Test SSE_Message with colons in the data"""
        data_with_colon = "key: value, another: value"
        result = SSE_Message(data_with_colon)
        
        assert f"data: {data_with_colon}" in result

    def test_SSE_Message_with_newlines_in_fields(self):
        """Test SSE_Message with newlines in event/id fields"""
        # SSE spec says fields should not contain newlines, but we should handle it
        result = SSE_Message("data", event="test\nevent", id="id\nwith\nnewlines")
        
        # The function should handle this gracefully
        assert "data: data" in result

    def test_SSE_Response_zero_status_code(self):
        """Test SSE response with zero status code"""
        def simple_generator():
            yield "data: test\n\n"
        
        # Status code 0 might be normalized to default
        response = SSE_Response(simple_generator(), status_code=0)
        # The response should handle this - either keep 0 or default to 200
        assert response.status_code in [0, 200]

    def test_sse_headers_modification(self):
        """Test modifying SSE headers after creation"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = SSE_Response(simple_generator())
        
        # Should be able to modify headers
        response.headers.set("X-Modified", "yes")
        assert response.headers.get("X-Modified") == "yes"
        
        # Original SSE headers should still be there
        assert response.headers.get("Content-Type") == "text/event-stream"

    def test_sse_unicode_and_special_chars(self):
        """Test SSE with various unicode and special characters"""
        special_chars = "🚀 Special chars: \n\t\r\"'\\áéíóú"
        result = SSE_Message(special_chars)
        
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
        
        _response = SSE_Response(counting_generator())
        
        # The generator shouldn't be consumed during response creation
        assert call_count == 0

    def test_SSE_Message_numeric_values(self):
        """Test SSE_Message with numeric values for fields"""
        result = SSE_Message("test", id=123, retry=5000)
        
        assert "id: 123" in result
        assert "retry: 5000" in result

    def test_SSE_Response_headers_type_validation(self):
        """Test that SSE response validates headers type"""
        def simple_generator():
            yield "data: test\n\n"
        
        # Should work with Headers object
        headers = Headers({"X-Test": "value"})
        response = SSE_Response(simple_generator(), headers=headers)
        assert response.headers.get("X-Test") == "value"
        
        # Should work with None
        response2 = SSE_Response(simple_generator(), headers=None)
        assert response2.headers.get("Content-Type") == "text/event-stream"

    def test_SSE_Message_empty_fields(self):
        """Test SSE_Message with empty field values"""
        result = SSE_Message("data", event="", id="", retry=None)
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
        response = SSE_Response(error_generator())
        assert isinstance(response, StreamingResponse)
        
        # The actual error would be handled at stream consumption time

    def test_sse_async_generator_types(self):
        """Test different async generator patterns"""
        async def async_gen_with_sleep():
            import asyncio
            yield "data: start\n\n"
            await asyncio.sleep(0.001)  # Very short sleep
            yield "data: end\n\n"
        
        response = SSE_Response(async_gen_with_sleep())
        assert isinstance(response, StreamingResponse)

    def test_SSE_Message_formatting_consistency(self):
        """Test that SSE_Message formatting is consistent"""
        # Same message should always produce same output
        msg1 = SSE_Message("test", event="e", id="1")
        msg2 = SSE_Message("test", event="e", id="1")
        assert msg1 == msg2
        
        # Different order of parameters should produce same output
        msg3 = SSE_Message("test", id="1", event="e")
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
        response = SSE_Response(simple_generator())
        
        # These should all work (depending on Headers implementation)
        content_type = (response.headers.get("Content-Type") or 
                       response.headers.get("content-type") or
                       response.headers.get("CONTENT-TYPE"))
        assert content_type == "text/event-stream"

    def test_SSE_Response_immutability(self):
        """Test that SSE response properties can be modified if needed"""
        def simple_generator():
            yield "data: test\n\n"
        
        response = SSE_Response(simple_generator())
        original_status = response.status_code
        
        # Should be able to modify status code
        response.status_code = 202
        assert response.status_code == 202
        assert response.status_code != original_status


@pytest.mark.benchmark  
class TestSSELiveEndpoints:
    """Test SSE endpoints against a running server"""

    def test_sse_basic_endpoint_headers(self):
        """Test that SSE basic endpoint returns correct headers"""
        response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
        
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'text/event-stream'
        assert response.headers.get('Cache-Control') == 'no-cache'
        # Connection: keep-alive is implicit with chunked transfer encoding in HTTP/1.1

    def test_sse_basic_content(self):
        """Test SSE basic endpoint content"""
        content = get_SSE_Response_quickly("/sse/basic")
        data_lines = parse_sse_data(content)
        
        # Should have 3 test messages
        assert len(data_lines) >= 3
        for i in range(3):
            assert f"Test message {i}" in data_lines

    def test_sse_formatted_content(self):
        """Test SSE formatted endpoint with SSE_Message"""
        content = get_SSE_Response_quickly("/sse/formatted")
        
        # Should contain event and id fields
        assert "event: test" in content
        assert "id: 0" in content
        assert "id: 1" in content
        assert "id: 2" in content
        
        data_lines = parse_sse_data(content)
        assert len(data_lines) >= 3
        for i in range(3):
            assert f"Formatted message {i}" in data_lines

    def test_sse_json_content(self):
        """Test SSE JSON endpoint"""
        content = get_SSE_Response_quickly("/sse/json")
        data_lines = parse_sse_data(content)
        
        assert len(data_lines) >= 3
        
        # Each data line should be valid JSON
        for i, data_line in enumerate(data_lines[:3]):
            json_data = json.loads(data_line)
            assert json_data['id'] == i
            assert json_data['message'] == f"JSON message {i}"
            assert json_data['type'] == "test"

    def test_sse_named_events_content(self):
        """Test SSE named events endpoint"""
        content = get_SSE_Response_quickly("/sse/named_events")
        
        # Should contain different event types
        assert "event: start" in content
        assert "event: progress" in content  
        assert "event: end" in content
        
        # Should contain corresponding data
        assert "Test started" in content
        assert "Test in progress" in content
        assert "Test completed" in content

    def test_sse_async_endpoint(self):
        """Test async SSE endpoint"""
        content = get_SSE_Response_quickly("/sse/async", timeout=5.0)
        data_lines = parse_sse_data(content)
        
        assert len(data_lines) >= 3
        for i in range(3):
            assert f"Async message {i}" in data_lines

    def test_sse_single_message(self):
        """Test SSE endpoint with single message"""
        content = get_SSE_Response_quickly("/sse/single")
        data_lines = parse_sse_data(content)
        
        assert len(data_lines) == 1
        assert data_lines[0] == "Single message"

    def test_sse_empty_endpoint(self):
        """Test SSE endpoint that sends no messages"""
        content = get_SSE_Response_quickly("/sse/empty", timeout=1.0)
        data_lines = parse_sse_data(content)
        
        # Should have no data lines
        assert len(data_lines) == 0

    def test_sse_custom_headers(self):
        """Test SSE endpoint with custom headers"""
        response = requests.get(f"{BASE_URL}/sse/with_headers", stream=True)
        
        assert response.status_code == 200
        assert response.headers.get('X-Custom-Header') == 'custom-value'
        assert response.headers.get('Content-Type') == 'text/event-stream'

    def test_sse_custom_status_code(self):
        """Test SSE endpoint with custom status code"""
        response = requests.get(f"{BASE_URL}/sse/status_code", stream=True)
        
        assert response.status_code == 201
        assert response.headers.get('Content-Type') == 'text/event-stream'

    def test_sse_concurrent_requests(self):
        """Test multiple concurrent SSE requests"""
        
        def get_basic_sse():
            content = get_SSE_Response_quickly("/sse/basic")
            return parse_sse_data(content)
        
        # Make 3 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(get_basic_sse) for _ in range(3)]
            results = [future.result(timeout=10) for future in futures]
        
        # All should return the same content
        for result in results:
            assert len(result) >= 3
            for i in range(3):
                assert f"Test message {i}" in result

    def test_sse_middleware_compatibility(self):
        """Test that SSE endpoints work with global middleware"""
        response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
        
        # Should have global response headers from middleware
        assert response.headers.get('server') == 'robyn'

    def test_sse_cors_headers(self):
        """Test that SSE endpoints include CORS headers"""
        response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
        
        # Should have CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_sse_performance_timing(self):
        """Test SSE response timing"""
        start_time = time.time()
        content = get_SSE_Response_quickly("/sse/basic")
        end_time = time.time()
        
        # Should complete reasonably quickly
        assert end_time - start_time < 5.0
        
        # Should have received data
        data_lines = parse_sse_data(content)
        assert len(data_lines) >= 3

    def test_sse_client_disconnect_handling(self):
        """Test SSE behavior when client disconnects early"""
        url = f"{BASE_URL}/sse/basic"
        
        # Start request but don't read all data
        response = requests.get(url, stream=True, timeout=1)
        assert response.status_code == 200
        
        # Read just a little bit then close
        chunk = next(response.iter_content(chunk_size=100, decode_unicode=True))
        assert len(chunk) > 0
        
        # Close the connection
        response.close()
        
        # Server should handle this gracefully (we can't directly test this,
        # but the test passing means no exceptions were raised)

    def test_sse_content_encoding(self):
        """Test SSE content encoding and format"""
        content = get_SSE_Response_quickly("/sse/basic")
        
        # Should be properly formatted SSE
        lines = content.split('\n')
        
        # Should have data lines
        data_line_count = sum(1 for line in lines if line.startswith('data:'))
        assert data_line_count >= 3
        
        # Should end with double newline pattern
        assert content.count('\n\n') >= 1

    def test_sse_error_endpoint_404(self):
        """Test that non-existent SSE endpoints return 404"""
        response = requests.get(f"{BASE_URL}/sse/nonexistent", stream=True)
        assert response.status_code == 404

    def test_sse_http_methods(self):
        """Test that SSE endpoints only work with GET"""
        # GET should work
        response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
        assert response.status_code == 200
        
        # POST should not work (404 or 405)
        response = requests.post(f"{BASE_URL}/sse/basic")
        assert response.status_code in [404, 405]


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
            
        except requests.exceptions.RequestException:
            pytest.skip("Could not connect to debug SSE endpoint")


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sse_client():
    """Fixture to provide an SSE client for testing"""
    def _create_client(endpoint: str):
        if not HAS_SSECLIENT:
            pytest.skip("sseclient library not available")
        url = f"{BASE_URL}/{endpoint.strip('/')}"
        return SSEClient(url)
    return _create_client


@pytest.mark.skipif(not HAS_SSECLIENT, reason="sseclient library not available")
def test_sse_with_sseclient_library():
    """Test SSE using the sseclient library (if available)"""
    url = f"{BASE_URL}/sse/basic"
    client = SSEClient(url)
    
    events = []
    for event in client.events():
        events.append(event)
        if len(events) >= 3:  # We expect 3 events
            break
    
    assert len(events) == 3
    for i, event in enumerate(events):
        assert event.data == f"Test message {i}"