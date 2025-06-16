#!/usr/bin/env python3
"""
Comprehensive test suite for Robyn's MCP (Model Context Protocol) implementation.

Tests cover:
- Core MCP protocol compliance
- URI template matching and parameter extraction
- Auto-generated schemas from function signatures
- JSON-RPC 2.0 message handling
- Error handling and edge cases
- Integration with Robyn app
"""

import asyncio
import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

# Import the MCP implementation
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robyn.mcp import (
    MCPHandler, MCPApp, MCPError, MCPResource, MCPTool, MCPPrompt,
    _extract_uri_params, _generate_schema_from_function, _generate_prompt_args_from_function
)
from robyn import Robyn


class TestURITemplateUtilities:
    """Test URI template parsing and schema generation utilities"""
    
    def test_extract_uri_params(self):
        """Test URI parameter extraction"""
        test_cases = [
            ("echo://{message}", ["message"]),
            ("user://{user_id}/profile", ["user_id"]),
            ("math://{operation}/{a}/{b}", ["operation", "a", "b"]),
            ("simple://static", []),
            ("complex://{id}/items/{item_id}/details", ["id", "item_id"]),
        ]
        
        for uri, expected in test_cases:
            result = _extract_uri_params(uri)
            assert result == expected, f"Failed for URI: {uri}"
    
    def test_generate_schema_from_function(self):
        """Test automatic schema generation from function signatures"""
        
        def simple_func(message: str) -> str:
            return message
        
        def complex_func(text: str, count: int = 1, active: bool = True) -> str:
            return f"{text} * {count}"
        
        def untyped_func(arg1, arg2="default"):
            return f"{arg1} {arg2}"
        
        # Test simple function
        schema = _generate_schema_from_function(simple_func)
        assert schema["type"] == "object"
        assert "message" in schema["properties"]
        assert schema["properties"]["message"]["type"] == "string"
        assert schema["required"] == ["message"]
        
        # Test complex function with different types
        schema = _generate_schema_from_function(complex_func)
        assert "text" in schema["properties"]
        assert "count" in schema["properties"] 
        assert "active" in schema["properties"]
        assert schema["properties"]["text"]["type"] == "string"
        assert schema["properties"]["count"]["type"] == "integer"
        assert schema["properties"]["active"]["type"] == "boolean"
        assert schema["required"] == ["text"]  # Only required param
        
        # Test untyped function (defaults to string)
        schema = _generate_schema_from_function(untyped_func)
        assert all(prop["type"] == "string" for prop in schema["properties"].values())
    
    def test_generate_prompt_args(self):
        """Test prompt argument generation"""
        
        def prompt_func(code: str, language: str = "python") -> str:
            return f"Explain this {language} code: {code}"
        
        args = _generate_prompt_args_from_function(prompt_func)
        
        assert len(args) == 2
        assert args[0]["name"] == "code"
        assert args[0]["required"] == True
        assert args[1]["name"] == "language" 
        assert args[1]["required"] == False


class TestMCPHandler:
    """Test the core MCP protocol handler"""
    
    @pytest.fixture
    def handler(self):
        """Create a fresh MCP handler for each test"""
        return MCPHandler()
    
    def test_handler_initialization(self, handler):
        """Test handler initializes correctly"""
        assert handler.resources == {}
        assert handler.tools == {}
        assert handler.prompts == {}
        assert handler.server_info["name"] == "robyn-mcp-server"
        assert handler.server_info["version"] == "1.0.0"
    
    def test_register_resource(self, handler):
        """Test resource registration"""
        def test_resource(params):
            return "test content"
        
        handler.register_resource(
            "test://example", 
            "Test Resource", 
            test_resource,
            "A test resource",
            "text/plain"
        )
        
        assert "test://example" in handler.resources
        assert "test://example" in handler.resource_metadata
        
        metadata = handler.resource_metadata["test://example"]
        assert metadata.uri == "test://example"
        assert metadata.name == "Test Resource"
        assert metadata.description == "A test resource"
        assert metadata.mimeType == "text/plain"
    
    def test_register_tool(self, handler):
        """Test tool registration"""
        def test_tool(args):
            return f"Tool result: {args}"
        
        schema = {"type": "object", "properties": {"input": {"type": "string"}}}
        
        handler.register_tool("test_tool", test_tool, "A test tool", schema)
        
        assert "test_tool" in handler.tools
        assert "test_tool" in handler.tool_metadata
        
        metadata = handler.tool_metadata["test_tool"]
        assert metadata.name == "test_tool"
        assert metadata.description == "A test tool"
        assert metadata.inputSchema == schema
    
    def test_register_prompt(self, handler):
        """Test prompt registration"""
        def test_prompt(args):
            return f"Prompt: {args}"
        
        arguments = [{"name": "input", "required": True}]
        
        handler.register_prompt("test_prompt", test_prompt, "A test prompt", arguments)
        
        assert "test_prompt" in handler.prompts
        assert "test_prompt" in handler.prompt_metadata
        
        metadata = handler.prompt_metadata["test_prompt"]
        assert metadata.name == "test_prompt"
        assert metadata.description == "A test prompt"
        assert metadata.arguments == arguments
    
    def test_uri_template_matching(self, handler):
        """Test URI template matching and parameter extraction"""
        def echo_handler(message):
            return f"Echo: {message}"
        
        def user_handler(user_id):
            return f"User: {user_id}"
        
        def math_handler(operation, a, b):
            return f"{operation}({a}, {b})"
        
        # Register templates
        handler.register_resource("echo://{message}", "Echo", echo_handler)
        handler.register_resource("user://{user_id}/profile", "User Profile", user_handler)
        handler.register_resource("math://{operation}/{a}/{b}", "Math", math_handler)
        
        # Test exact matches
        result = handler._match_uri_template("echo://hello")
        assert result is not None
        assert result[0] == "echo://{message}"
        assert result[1] == {"message": "hello"}
        
        # Test path parameters (should work with the fix)
        result = handler._match_uri_template("echo://hello/world")
        assert result is not None
        assert result[1] == {"message": "hello/world"}
        
        # Test multiple parameters
        result = handler._match_uri_template("math://add/5/3")
        assert result is not None
        assert result[1] == {"operation": "add", "a": "5", "b": "3"}
        
        # Test no match
        result = handler._match_uri_template("unknown://test")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_initialize_request(self, handler):
        """Test MCP initialize request"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = await handler.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
        result = response["result"]
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "robyn-mcp-server"
    
    @pytest.mark.asyncio
    async def test_list_resources(self, handler):
        """Test resources/list request"""
        # Register a test resource
        handler.register_resource("test://example", "Test", lambda: "test")
        
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {}
        }
        
        response = await handler.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        
        resources = response["result"]["resources"]
        assert len(resources) == 1
        assert resources[0]["uri"] == "test://example"
        assert resources[0]["name"] == "Test"
    
    @pytest.mark.asyncio
    async def test_read_resource(self, handler):
        """Test resources/read request"""
        def test_resource(message):
            return f"Content: {message}"
        
        handler.register_resource("test://{message}", "Test", test_resource)
        
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/read",
            "params": {"uri": "test://hello"}
        }
        
        response = await handler.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        
        contents = response["result"]["contents"]
        assert len(contents) == 1
        assert contents[0]["uri"] == "test://hello"
        assert contents[0]["text"] == "Content: hello"
    
    @pytest.mark.asyncio
    async def test_call_tool(self, handler):
        """Test tools/call request"""
        def calculator(expression):
            return str(eval(expression, {"__builtins__": {}}, {}))
        
        schema = {"type": "object", "properties": {"expression": {"type": "string"}}}
        handler.register_tool("calculate", calculator, "Calculator", schema)
        
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "calculate",
                "arguments": {"expression": "2 + 2"}
            }
        }
        
        response = await handler.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response
        
        content = response["result"]["content"]
        assert len(content) == 1
        assert content[0]["text"] == "4"
    
    @pytest.mark.asyncio
    async def test_get_prompt(self, handler):
        """Test prompts/get request"""
        def code_review(code, language="python"):
            return f"Please review this {language} code: {code}"
        
        handler.register_prompt("code_review", code_review, "Code Review", [])
        
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "prompts/get",
            "params": {
                "name": "code_review",
                "arguments": {"code": "print('hello')", "language": "python"}
            }
        }
        
        response = await handler.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response
        
        result = response["result"]
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "Please review this python code: print('hello')" in result["messages"][0]["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, handler):
        """Test error responses"""
        # Test unknown method
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "unknown/method",
            "params": {}
        }
        
        response = await handler.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found
        
        # Test missing resource
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/read",
            "params": {"uri": "nonexistent://test"}
        }
        
        response = await handler.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32602  # Invalid params
    
    @pytest.mark.asyncio
    async def test_async_handlers(self, handler):
        """Test async function handlers"""
        async def async_resource():
            await asyncio.sleep(0.01)  # Simulate async work
            return "async content"
        
        async def async_tool(message):
            await asyncio.sleep(0.01)
            return f"async: {message}"
        
        handler.register_resource("async://test", "Async Test", async_resource)
        handler.register_tool("async_tool", async_tool, "Async Tool", {
            "type": "object",
            "properties": {"message": {"type": "string"}}
        })
        
        # Test async resource
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "async://test"}
        }
        
        response = await handler.handle_request(request)
        assert response["result"]["contents"][0]["text"] == "async content"
        
        # Test async tool
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "async_tool",
                "arguments": {"message": "hello"}
            }
        }
        
        response = await handler.handle_request(request)
        assert response["result"]["content"][0]["text"] == "async: hello"


class TestMCPApp:
    """Test the MCP app integration with Robyn"""
    
    @pytest.fixture
    def app(self):
        """Create a test Robyn app with MCP"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file = f.name
        
        try:
            app = Robyn(temp_file)
            yield app
        finally:
            os.unlink(temp_file)
    
    def test_mcp_property_initialization(self, app):
        """Test that app.mcp property initializes correctly"""
        mcp = app.mcp
        assert isinstance(mcp, MCPApp)
        assert mcp.app == app
        assert isinstance(mcp.handler, MCPHandler)
        
        # Second access should return same instance
        mcp2 = app.mcp
        assert mcp is mcp2
    
    def test_simplified_resource_decorator(self, app):
        """Test simplified resource decorator syntax"""
        
        @app.mcp.resource("echo://{message}")
        def echo_resource(message: str) -> str:
            """Echo a message"""
            return f"Echo: {message}"
        
        # Check that resource was registered
        assert "echo://{message}" in app.mcp.handler.resources
        metadata = app.mcp.handler.resource_metadata["echo://{message}"]
        assert metadata.name == "Echo Resource"  # Auto-generated from function name
        assert metadata.description == "Echo a message"  # From docstring
        assert metadata.mimeType == "text/plain"  # Default
    
    def test_simplified_tool_decorator(self, app):
        """Test simplified tool decorator syntax"""
        
        @app.mcp.tool()
        def calculate(expression: str, precision: int = 2) -> str:
            """Calculate mathematical expressions"""
            result = eval(expression, {"__builtins__": {}}, {})
            return f"{expression} = {round(result, precision)}"
        
        # Check that tool was registered
        assert "calculate" in app.mcp.handler.tools
        metadata = app.mcp.handler.tool_metadata["calculate"]
        assert metadata.name == "calculate"
        assert metadata.description == "Calculate mathematical expressions"
        
        # Check auto-generated schema
        schema = metadata.inputSchema
        assert "expression" in schema["properties"]
        assert "precision" in schema["properties"]
        assert schema["properties"]["expression"]["type"] == "string"
        assert schema["properties"]["precision"]["type"] == "integer"
        assert schema["required"] == ["expression"]
    
    def test_simplified_prompt_decorator(self, app):
        """Test simplified prompt decorator syntax"""
        
        @app.mcp.prompt()
        def explain_code(code: str, language: str = "python") -> str:
            """Generate code explanation prompt"""
            return f"Please explain this {language} code: {code}"
        
        # Check that prompt was registered
        assert "explain_code" in app.mcp.handler.prompts
        metadata = app.mcp.handler.prompt_metadata["explain_code"]
        assert metadata.name == "explain_code"
        assert metadata.description == "Generate code explanation prompt"
        
        # Check auto-generated arguments
        args = metadata.arguments
        assert len(args) == 2
        assert args[0]["name"] == "code"
        assert args[0]["required"] == True
        assert args[1]["name"] == "language"
        assert args[1]["required"] == False
    
    def test_custom_parameters(self, app):
        """Test decorators with custom parameters"""
        
        @app.mcp.resource("file://{path}", "Custom File Reader", "Read files", "text/markdown")
        def read_file(path: str) -> str:
            return f"File content: {path}"
        
        @app.mcp.tool("custom_tool", "Custom description", {
            "type": "object",
            "properties": {"input": {"type": "string"}},
            "required": ["input"]
        })
        def custom_tool(input: str) -> str:
            return f"Custom: {input}"
        
        # Check custom resource
        metadata = app.mcp.handler.resource_metadata["file://{path}"]
        assert metadata.name == "Custom File Reader"
        assert metadata.description == "Read files"
        assert metadata.mimeType == "text/markdown"
        
        # Check custom tool
        metadata = app.mcp.handler.tool_metadata["custom_tool"]
        assert metadata.name == "custom_tool"
        assert metadata.description == "Custom description"
        assert metadata.inputSchema["properties"]["input"]["type"] == "string"


class TestIntegration:
    """Integration tests for the complete MCP system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test a complete MCP workflow from registration to execution"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file = f.name
        
        try:
            app = Robyn(temp_file)
            
            # Register various MCP capabilities
            @app.mcp.resource("echo://{message}")
            def echo_resource(message: str) -> str:
                return f"Resource: {message}"
            
            @app.mcp.tool()
            def greet(name: str, formal: bool = False) -> str:
                if formal:
                    return f"Good day, {name}"
                return f"Hi {name}!"
            
            @app.mcp.prompt()
            def task_prompt(task: str, priority: str = "medium") -> str:
                return f"Please help me with this {priority} priority task: {task}"
            
            handler = app.mcp.handler
            
            # Test the complete workflow
            
            # 1. Initialize
            init_response = await handler.handle_request({
                "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}
            })
            assert "result" in init_response
            
            # 2. List resources
            list_response = await handler.handle_request({
                "jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}
            })
            assert len(list_response["result"]["resources"]) == 1
            
            # 3. Read resource with URI template
            read_response = await handler.handle_request({
                "jsonrpc": "2.0", "id": 3, "method": "resources/read",
                "params": {"uri": "echo://hello/world"}
            })
            assert read_response["result"]["contents"][0]["text"] == "Resource: hello/world"
            
            # 4. List tools
            tools_response = await handler.handle_request({
                "jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}
            })
            assert len(tools_response["result"]["tools"]) == 1
            
            # 5. Call tool
            call_response = await handler.handle_request({
                "jsonrpc": "2.0", "id": 5, "method": "tools/call",
                "params": {"name": "greet", "arguments": {"name": "Alice", "formal": True}}
            })
            assert call_response["result"]["content"][0]["text"] == "Good day, Alice"
            
            # 6. Get prompt
            prompt_response = await handler.handle_request({
                "jsonrpc": "2.0", "id": 6, "method": "prompts/get",
                "params": {"name": "task_prompt", "arguments": {"task": "review code", "priority": "high"}}
            })
            message_text = prompt_response["result"]["messages"][0]["content"]["text"]
            assert "high priority task: review code" in message_text
            
        finally:
            os.unlink(temp_file)
    
    def test_knowledge_assistant_patterns(self):
        """Test the patterns used in the knowledge assistant example"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file = f.name
        
        try:
            app = Robyn(temp_file)
            
            # File system pattern
            @app.mcp.resource("fs://{path}")
            def read_file(path: str) -> str:
                return f"File content: {path}"
            
            # Git repository pattern
            @app.mcp.resource("git://repo/{repo_name}")
            def git_info(repo_name: str) -> str:
                return f"Git info: {repo_name}"
            
            # System monitoring pattern
            @app.mcp.resource("system://stats")
            def system_stats() -> str:
                return "System statistics"
            
            # Note creation tool
            @app.mcp.tool()
            def create_note(title: str, content: str, tags: str = "") -> str:
                return f"Note '{title}' created with tags: {tags}"
            
            # File search tool
            @app.mcp.tool()
            def search_files(query: str, directory: str = "") -> str:
                return f"Searched for '{query}' in {directory or 'all directories'}"
            
            # Code analysis prompt
            @app.mcp.prompt()
            def analyze_code(file_path: str, focus: str = "general") -> str:
                return f"Analyze {file_path} focusing on {focus}"
            
            handler = app.mcp.handler
            
            # Verify all registrations
            assert len(handler.resources) == 3
            assert len(handler.tools) == 2
            assert len(handler.prompts) == 1
            
            # Test URI templates work with realistic paths
            match = handler._match_uri_template("fs://Documents/projects/web-app/src/main.py")
            assert match is not None
            assert match[1]["path"] == "Documents/projects/web-app/src/main.py"
            
            match = handler._match_uri_template("git://repo/my-awesome-project")
            assert match is not None
            assert match[1]["repo_name"] == "my-awesome-project"
            
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    # Run tests manually if called directly
    import subprocess
    subprocess.run(["python", "-m", "pytest", __file__, "-v"])