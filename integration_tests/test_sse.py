import json
import pytest
import requests
from requests import Response

from integration_tests.helpers.http_methods_helpers import get, BASE_URL
from robyn.responses import SSE_Response, SSE_Message, StreamingResponse


@pytest.mark.benchmark
def test_sse_basic_headers(session):
    """Test that SSE endpoints return correct headers"""
    response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
    
    assert response.status_code == 200
    assert response.headers.get('Content-Type') == 'text/event-stream'
    assert response.headers.get('Cache-Control') == 'no-cache'
    assert 'Access-Control-Allow-Origin' in response.headers


@pytest.mark.benchmark
def test_sse_basic_stream(session):
    """Test basic SSE streaming with simple data messages"""
    response = requests.get(f"{BASE_URL}/sse/basic", stream=True, timeout=5)
    response.raise_for_status()
    
    content = ""
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            content += chunk
        if content.count('\n\n') >= 3:  # Got 3 messages
            break
    
    # Parse events
    events = []
    for line in content.split('\n'):
        if line.startswith('data: '):
            events.append(line[6:])  # Remove 'data: ' prefix
    
    assert len(events) >= 3
    for i in range(3):
        assert f"Test message {i}" in events


@pytest.mark.benchmark
def test_sse_formatted_messages(session):
    """Test SSE messages formatted with SSE_Message helper"""
    response = requests.get(f"{BASE_URL}/sse/formatted", stream=True, timeout=5)
    response.raise_for_status()
    
    content = ""
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            content += chunk
        if content.count('\n\n') >= 3:
            break
    
    # Should contain event and id fields
    assert "event: test" in content
    assert "id: 0" in content
    assert "id: 1" in content
    assert "id: 2" in content
    
    # Parse data lines
    data_lines = []
    for line in content.split('\n'):
        if line.startswith('data: '):
            data_lines.append(line[6:])
    
    assert len(data_lines) >= 3
    for i in range(3):
        assert f"Formatted message {i}" in data_lines


@pytest.mark.benchmark
def test_sse_json_data(session):
    """Test SSE streaming with JSON data"""
    response = requests.get(f"{BASE_URL}/sse/json", stream=True, timeout=5)
    response.raise_for_status()
    
    content = ""
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            content += chunk
        if content.count('\n\n') >= 3:
            break
    
    # Parse data lines
    data_lines = []
    for line in content.split('\n'):
        if line.startswith('data: '):
            data_lines.append(line[6:])
    
    assert len(data_lines) >= 3
    for i in range(3):
        json_data = json.loads(data_lines[i])
        assert json_data['id'] == i
        assert json_data['message'] == f"JSON message {i}"
        assert json_data['type'] == "test"


@pytest.mark.benchmark
def test_sse_named_events(session):
    """Test SSE with different event types"""
    response = requests.get(f"{BASE_URL}/sse/named_events", stream=True, timeout=5)
    response.raise_for_status()
    
    content = ""
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            content += chunk
        if content.count('\n\n') >= 3:
            break
    
    # Should contain different event types
    assert "event: start" in content
    assert "event: progress" in content
    assert "event: end" in content
    
    # Should contain corresponding data
    assert "data: Test started" in content
    assert "data: Test in progress" in content
    assert "data: Test completed" in content


@pytest.mark.benchmark
def test_sse_async_endpoint(session):
    """Test async SSE endpoint"""
    response = requests.get(f"{BASE_URL}/sse/async", stream=True, timeout=5)
    response.raise_for_status()
    
    content = ""
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            content += chunk
        if content.count('\n\n') >= 3:
            break
    
    # Parse data lines
    data_lines = []
    for line in content.split('\n'):
        if line.startswith('data: '):
            data_lines.append(line[6:])
    
    assert len(data_lines) >= 3
    for i in range(3):
        assert f"Async message {i}" in data_lines


@pytest.mark.benchmark
def test_sse_single_message(session):
    """Test SSE endpoint that sends only one message"""
    response = requests.get(f"{BASE_URL}/sse/single", stream=True, timeout=3)
    response.raise_for_status()
    
    content = ""
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            content += chunk
        if '\n\n' in content:  # Got at least one message
            break
    
    # Parse data lines
    data_lines = []
    for line in content.split('\n'):
        if line.startswith('data: '):
            data_lines.append(line[6:])
    
    assert len(data_lines) == 1
    assert data_lines[0] == "Single message"


@pytest.mark.benchmark
def test_sse_empty_stream(session):
    """Test SSE endpoint that sends no messages"""
    response = requests.get(f"{BASE_URL}/sse/empty", stream=True, timeout=2)
    response.raise_for_status()
    
    content = ""
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            content += chunk
        # Don't wait forever for empty stream
        break
    
    # Parse data lines
    data_lines = []
    for line in content.split('\n'):
        if line.startswith('data: '):
            data_lines.append(line[6:])
    
    assert len(data_lines) == 0


@pytest.mark.benchmark
def test_sse_custom_headers(session):
    """Test SSE endpoint with custom headers"""
    response = requests.get(f"{BASE_URL}/sse/with_headers", stream=True)
    
    assert response.status_code == 200
    assert response.headers.get('X-Custom-Header') == 'custom-value'
    assert response.headers.get('Content-Type') == 'text/event-stream'


@pytest.mark.benchmark
def test_sse_custom_status_code(session):
    """Test SSE endpoint with custom status code"""
    response = requests.get(f"{BASE_URL}/sse/status_code", stream=True)
    
    assert response.status_code == 201
    assert response.headers.get('Content-Type') == 'text/event-stream'


@pytest.mark.benchmark
def test_sse_middleware_compatibility(session):
    """Test that SSE endpoints work with global middleware"""
    response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
    
    # Should have global response headers from middleware
    assert response.headers.get('server') == 'robyn'


def test_sse_message_formatter():
    """Test the SSE_Message formatter utility function"""
    
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


def test_sse_message_edge_cases():
    """Test SSE_Message with edge cases"""
    
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
    
    # Test message with special characters
    special_message = "Hello\nWorld\r\nWith\tTabs"
    result = SSE_Message(special_message)
    assert "data: Hello\ndata: World\ndata: With\tTabs\n\n" in result


def test_sse_response_classes():
    """Test that SSE response classes can be imported correctly"""
    assert SSE_Response is not None
    assert SSE_Message is not None
    assert StreamingResponse is not None
    
    # Test basic functionality
    def simple_generator():
        yield "data: test\n\n"
    
    response = SSE_Response(simple_generator())
    assert response.media_type == "text/event-stream"
    assert response.status_code == 200


def test_sse_error_handling():
    """Test error handling in SSE streams"""
    # Test with a non-existent endpoint
    response = requests.get(f"{BASE_URL}/sse/nonexistent", stream=True)
    assert response.status_code == 404


def test_sse_http_methods():
    """Test that SSE endpoints only work with GET"""
    # GET should work
    response = requests.get(f"{BASE_URL}/sse/basic", stream=True)
    assert response.status_code == 200
    
    # POST should not work (404 or 405)
    response = requests.post(f"{BASE_URL}/sse/basic")
    assert response.status_code in [404, 405]
