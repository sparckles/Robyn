# Test live SSE endpoints 
# These tests require the test server to be running

import json
import time
import threading
from typing import List, Dict, Any

import pytest
import requests

from integration_tests.helpers.http_methods_helpers import BASE_URL


def parse_sse_data(text: str) -> List[str]:
    """Parse SSE data lines from response text"""
    data_lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('data: '):
            data_lines.append(line[6:])  # Remove 'data: ' prefix
    return data_lines


def get_sse_response_quickly(endpoint: str, timeout: float = 3.0) -> str:
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
        content = get_sse_response_quickly("/sse/basic")
        data_lines = parse_sse_data(content)
        
        # Should have 3 test messages
        assert len(data_lines) >= 3
        for i in range(3):
            assert f"Test message {i}" in data_lines

    def test_sse_formatted_content(self):
        """Test SSE formatted endpoint with sse_message"""
        content = get_sse_response_quickly("/sse/formatted")
        
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
        content = get_sse_response_quickly("/sse/json")
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
        content = get_sse_response_quickly("/sse/named_events")
        
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
        content = get_sse_response_quickly("/sse/async", timeout=5.0)
        data_lines = parse_sse_data(content)
        
        assert len(data_lines) >= 3
        for i in range(3):
            assert f"Async message {i}" in data_lines

    def test_sse_single_message(self):
        """Test SSE endpoint with single message"""
        content = get_sse_response_quickly("/sse/single")
        data_lines = parse_sse_data(content)
        
        assert len(data_lines) == 1
        assert data_lines[0] == "Single message"

    def test_sse_empty_endpoint(self):
        """Test SSE endpoint that sends no messages"""
        content = get_sse_response_quickly("/sse/empty", timeout=1.0)
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
        import concurrent.futures
        
        def get_basic_sse():
            content = get_sse_response_quickly("/sse/basic")
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
        content = get_sse_response_quickly("/sse/basic")
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
        content = get_sse_response_quickly("/sse/basic")
        
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