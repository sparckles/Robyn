# Test Server-Sent Events (SSE) functionality
# Tests both basic SSE streams and formatted events

import json
import threading
import time
from typing import List, Dict, Any
from unittest.mock import patch
import re

import pytest
import requests

from integration_tests.helpers.http_methods_helpers import BASE_URL

# Try to import sseclient, but don't fail if it's not available
try:
    from sseclient import SSEClient
    HAS_SSECLIENT = True
except ImportError:
    SSEClient = None
    HAS_SSECLIENT = False


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


class TestServerSentEvents:
    """Test class for Server-Sent Events functionality"""

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
        """Test SSE messages formatted with sse_message helper"""
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

    def test_sse_response_class_import(self):
        """Test that SSE classes can be imported correctly"""
        try:
            from robyn import sse_response, sse_message, StreamingResponse
            assert sse_response is not None
            assert sse_message is not None
            assert StreamingResponse is not None
        except ImportError as e:
            pytest.fail(f"Failed to import SSE classes: {e}")

    def test_sse_message_formatter(self):
        """Test the sse_message formatter utility function"""
        from robyn import sse_message
        
        # Test basic message
        result = sse_message("Hello world")
        assert "data: Hello world\n\n" in result
        
        # Test with event type
        result = sse_message("Hello", event="greeting")
        assert "event: greeting\n" in result
        assert "data: Hello\n\n" in result
        
        # Test with ID
        result = sse_message("Hello", id="123")
        assert "id: 123\n" in result
        assert "data: Hello\n\n" in result
        
        # Test with retry
        result = sse_message("Hello", retry=5000)
        assert "retry: 5000\n" in result
        assert "data: Hello\n\n" in result
        
        # Test with all parameters
        result = sse_message("Hello", event="test", id="456", retry=3000)
        assert "event: test\n" in result
        assert "id: 456\n" in result
        assert "retry: 3000\n" in result
        assert "data: Hello\n\n" in result
        
        # Test multiline data
        result = sse_message("Line 1\nLine 2")
        assert "data: Line 1\ndata: Line 2\n\n" in result

    def test_sse_concurrent_connections(self):
        """Test multiple concurrent SSE connections"""
        import concurrent.futures
        
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


# Test fixtures and utilities for SSE testing

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