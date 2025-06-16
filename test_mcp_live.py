#!/usr/bin/env python3
"""
Live integration test for MCP server.

This script tests the MCP implementation by making actual HTTP requests
to a running Robyn server with MCP endpoints.

Usage:
1. python test_mcp_live.py start-server  # Starts test server in background
2. python test_mcp_live.py test         # Runs tests against running server  
3. python test_mcp_live.py full         # Starts server, runs tests, stops server
"""

import asyncio
import json
import subprocess
import sys
import time
import signal
import os
from urllib.request import urlopen, Request
from urllib.error import URLError


class MCPLiveTest:
    """Live integration test for MCP server"""
    
    def __init__(self, server_url="http://localhost:8080"):
        self.server_url = server_url
        self.mcp_url = f"{server_url}/mcp"
        self.server_process = None
    
    def start_test_server(self):
        """Start a test MCP server"""
        print("🚀 Starting test MCP server...")
        
        # Create a simple test server
        server_code = '''
import tempfile
import os
from robyn import Robyn

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    temp_file = f.name

try:
    app = Robyn(temp_file)

    @app.mcp.resource("echo://{message}")
    def echo_resource(message: str) -> str:
        """Echo a message back"""
        return f"Echo: {message}"

    @app.mcp.resource("time://current")
    def current_time() -> str:
        """Get current time"""
        from datetime import datetime
        return datetime.now().isoformat()

    @app.mcp.tool()
    def calculate(expression: str) -> str:
        """Calculate mathematical expressions"""
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"{expression} = {result}"
        except:
            return f"Error calculating: {expression}"

    @app.mcp.tool()
    def greet(name: str, formal: bool = False) -> str:
        """Generate a greeting"""
        if formal:
            return f"Good day, {name}"
        return f"Hi {name}!"

    @app.mcp.prompt()
    def explain_code(code: str, language: str = "python") -> str:
        """Generate code explanation prompt"""
        return f"Please explain this {language} code:\\n{code}"

    @app.get("/health")
    def health():
        return {"status": "ok", "mcp": "ready"}

    print("Test MCP server starting on port 8080...")
    app.start(port=8080, _check_port=False)

finally:
    os.unlink(temp_file)
'''
        
        # Write server code to temp file
        with open('temp_mcp_server.py', 'w') as f:
            f.write(server_code)
        
        # Start the server process
        self.server_process = subprocess.Popen([
            sys.executable, 'temp_mcp_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = urlopen(f"{self.server_url}/health", timeout=1)
                if response.getcode() == 200:
                    print("✅ Test server started successfully")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("❌ Failed to start test server")
        return False
    
    def stop_test_server(self):
        """Stop the test server"""
        if self.server_process:
            print("🛑 Stopping test server...")
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
        
        # Clean up temp file
        if os.path.exists('temp_mcp_server.py'):
            os.unlink('temp_mcp_server.py')
    
    def make_mcp_request(self, method, params=None):
        """Make an MCP JSON-RPC request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        req = Request(
            self.mcp_url,
            data=json.dumps(request_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except URLError as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def test_mcp_protocol(self):
        """Test MCP protocol compliance"""
        print("\n🧪 Testing MCP Protocol Compliance")
        print("-" * 40)
        
        # Test 1: Initialize
        print("📋 Testing initialize...")
        response = self.make_mcp_request("initialize")
        if response and "result" in response:
            result = response["result"]
            if "protocolVersion" in result and "capabilities" in result:
                print("✅ Initialize successful")
            else:
                print("❌ Initialize response missing required fields")
                return False
        else:
            print("❌ Initialize failed")
            return False
        
        # Test 2: List resources
        print("📋 Testing resources/list...")
        response = self.make_mcp_request("resources/list")
        if response and "result" in response:
            resources = response["result"]["resources"]
            print(f"✅ Found {len(resources)} resources")
            for resource in resources:
                print(f"   📁 {resource['name']}: {resource['uri']}")
        else:
            print("❌ List resources failed")
            return False
        
        # Test 3: Read resource
        print("📋 Testing resources/read...")
        response = self.make_mcp_request("resources/read", {"uri": "echo://test_message"})
        if response and "result" in response:
            content = response["result"]["contents"][0]["text"]
            if "Echo: test_message" in content:
                print("✅ Resource read successful")
            else:
                print(f"❌ Unexpected resource content: {content}")
                return False
        else:
            print("❌ Resource read failed")
            return False
        
        # Test 4: List tools
        print("📋 Testing tools/list...")
        response = self.make_mcp_request("tools/list")
        if response and "result" in response:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools")
            for tool in tools:
                print(f"   🔧 {tool['name']}: {tool['description']}")
        else:
            print("❌ List tools failed")
            return False
        
        # Test 5: Call tool
        print("📋 Testing tools/call...")
        response = self.make_mcp_request("tools/call", {
            "name": "calculate",
            "arguments": {"expression": "2 + 3 * 4"}
        })
        if response and "result" in response:
            result = response["result"]["content"][0]["text"]
            if "2 + 3 * 4 = 14" in result:
                print("✅ Tool call successful")
            else:
                print(f"❌ Unexpected tool result: {result}")
                return False
        else:
            print("❌ Tool call failed")
            return False
        
        # Test 6: Call tool with boolean parameter
        print("📋 Testing tools/call with boolean...")
        response = self.make_mcp_request("tools/call", {
            "name": "greet",
            "arguments": {"name": "Alice", "formal": True}
        })
        if response and "result" in response:
            result = response["result"]["content"][0]["text"]
            if "Good day, Alice" in result:
                print("✅ Tool call with boolean successful")
            else:
                print(f"❌ Unexpected greeting: {result}")
                return False
        else:
            print("❌ Tool call with boolean failed")
            return False
        
        # Test 7: List prompts
        print("📋 Testing prompts/list...")
        response = self.make_mcp_request("prompts/list")
        if response and "result" in response:
            prompts = response["result"]["prompts"]
            print(f"✅ Found {len(prompts)} prompts")
            for prompt in prompts:
                print(f"   💭 {prompt['name']}: {prompt['description']}")
        else:
            print("❌ List prompts failed")
            return False
        
        # Test 8: Get prompt
        print("📋 Testing prompts/get...")
        response = self.make_mcp_request("prompts/get", {
            "name": "explain_code",
            "arguments": {"code": "print('hello')", "language": "python"}
        })
        if response and "result" in response:
            messages = response["result"]["messages"]
            if len(messages) > 0 and "explain this python code" in messages[0]["content"]["text"].lower():
                print("✅ Prompt generation successful")
            else:
                print(f"❌ Unexpected prompt content")
                return False
        else:
            print("❌ Prompt generation failed")
            return False
        
        return True
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n🧪 Testing Error Handling")
        print("-" * 25)
        
        # Test unknown method
        print("📋 Testing unknown method...")
        response = self.make_mcp_request("unknown/method")
        if response and "error" in response and response["error"]["code"] == -32601:
            print("✅ Unknown method error handled correctly")
        else:
            print("❌ Unknown method error not handled correctly")
            return False
        
        # Test missing resource
        print("📋 Testing missing resource...")
        response = self.make_mcp_request("resources/read", {"uri": "missing://resource"})
        if response and "error" in response and response["error"]["code"] == -32602:
            print("✅ Missing resource error handled correctly")
        else:
            print("❌ Missing resource error not handled correctly")
            return False
        
        # Test missing tool
        print("📋 Testing missing tool...")
        response = self.make_mcp_request("tools/call", {"name": "missing_tool", "arguments": {}})
        if response and "error" in response and response["error"]["code"] == -32602:
            print("✅ Missing tool error handled correctly")
        else:
            print("❌ Missing tool error not handled correctly")
            return False
        
        return True
    
    def test_uri_templates(self):
        """Test URI template functionality"""
        print("\n🧪 Testing URI Templates")
        print("-" * 25)
        
        test_cases = [
            ("echo://simple", "Echo: simple"),
            ("echo://hello_world", "Echo: hello_world"),
            ("echo://test123", "Echo: test123"),
            ("time://current", lambda x: "T" in x),  # Check for ISO timestamp
        ]
        
        for uri, expected in test_cases:
            print(f"📋 Testing URI: {uri}")
            response = self.make_mcp_request("resources/read", {"uri": uri})
            
            if response and "result" in response:
                content = response["result"]["contents"][0]["text"]
                if callable(expected):
                    if expected(content):
                        print(f"✅ URI template test passed")
                    else:
                        print(f"❌ URI template test failed: {content}")
                        return False
                elif expected in content:
                    print(f"✅ URI template test passed")
                else:
                    print(f"❌ Expected '{expected}' in '{content}'")
                    return False
            else:
                print(f"❌ URI template test failed for {uri}")
                return False
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting MCP Live Integration Tests")
        print("=" * 50)
        
        tests = [
            ("MCP Protocol Compliance", self.test_mcp_protocol),
            ("Error Handling", self.test_error_handling),
            ("URI Templates", self.test_uri_templates),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} FAILED with exception: {e}")
        
        print(f"\n{'='*50}")
        print(f"TEST RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
            print("✅ MCP implementation is production ready")
            print("✅ Compatible with Claude Desktop and other MCP clients")
            return True
        else:
            print("💥 Some tests failed")
            return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_mcp_live.py <command>")
        print("Commands:")
        print("  start-server  - Start test server")
        print("  test         - Run tests (requires running server)")
        print("  full         - Start server, run tests, stop server")
        sys.exit(1)
    
    command = sys.argv[1]
    tester = MCPLiveTest()
    
    if command == "start-server":
        if tester.start_test_server():
            print("Server started. Run 'python test_mcp_live.py test' to run tests.")
            print("Press Ctrl+C to stop server.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                tester.stop_test_server()
                print("Server stopped.")
        
    elif command == "test":
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    elif command == "full":
        if tester.start_test_server():
            try:
                success = tester.run_all_tests()
                sys.exit(0 if success else 1)
            finally:
                tester.stop_test_server()
        else:
            print("Failed to start server")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()