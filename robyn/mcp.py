"""
Model Context Protocol (MCP) implementation for Robyn.

This module provides MCP server functionality following the JSON-RPC 2.0 specification.
It allows Robyn applications to serve as MCP servers, exposing resources, tools, and prompts
to MCP clients like Claude Desktop or other AI applications.
"""

import asyncio
import inspect
import json
import logging
import re
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def _extract_uri_params(uri: str) -> List[str]:
    """Extract parameter names from URI template like 'echo://{message}'"""
    return re.findall(r"\{(\w+)\}", uri)


def _generate_schema_from_function(func: Callable) -> Dict[str, Any]:
    """Generate JSON schema from function signature"""
    sig = inspect.signature(func)
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        # Skip 'self' parameter
        if param_name == "self":
            continue

        param_schema = {"type": "string"}  # Default to string

        # Try to infer type from annotation
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == str:
                param_schema["type"] = "string"
            elif param.annotation == int:
                param_schema["type"] = "integer"
            elif param.annotation == float:
                param_schema["type"] = "number"
            elif param.annotation == bool:
                param_schema["type"] = "boolean"
            elif hasattr(param.annotation, "__origin__"):
                # Handle generic types like List, Dict, etc.
                param_schema["type"] = "object"

        properties[param_name] = param_schema

        # Add to required if no default value
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {"type": "object", "properties": properties, "required": required}


def _generate_prompt_args_from_function(func: Callable) -> List[Dict[str, Any]]:
    """Generate prompt arguments from function signature"""
    sig = inspect.signature(func)
    arguments = []

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        arg_def = {"name": param_name, "description": f"Parameter {param_name}", "required": param.default == inspect.Parameter.empty}
        arguments.append(arg_def)

    return arguments


@dataclass
class MCPResource:
    """Represents an MCP resource"""

    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


@dataclass
class MCPTool:
    """Represents an MCP tool"""

    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class MCPPrompt:
    """Represents an MCP prompt template"""

    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None


@dataclass
class MCPMessage:
    """JSON-RPC 2.0 message structure"""

    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPError(Exception):
    """MCP-specific error"""

    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class MCPHandler:
    """Handles MCP protocol requests and responses"""

    def __init__(self):
        self.resources: Dict[str, Callable] = {}
        self.tools: Dict[str, Callable] = {}
        self.prompts: Dict[str, Callable] = {}
        self.resource_metadata: Dict[str, MCPResource] = {}
        self.tool_metadata: Dict[str, MCPTool] = {}
        self.prompt_metadata: Dict[str, MCPPrompt] = {}
        self.server_info = {"name": "robyn-mcp-server", "version": "1.0.0"}

    def register_resource(self, uri: str, name: str, handler: Callable, description: Optional[str] = None, mime_type: Optional[str] = None):
        """Register a resource handler"""
        self.resources[uri] = handler
        self.resource_metadata[uri] = MCPResource(uri=uri, name=name, description=description, mimeType=mime_type)

    def register_tool(self, name: str, handler: Callable, description: str, input_schema: Dict[str, Any]):
        """Register a tool handler"""
        self.tools[name] = handler
        self.tool_metadata[name] = MCPTool(name=name, description=description, inputSchema=input_schema)

    def register_prompt(self, name: str, handler: Callable, description: str, arguments: Optional[List[Dict[str, Any]]] = None):
        """Register a prompt handler"""
        self.prompts[name] = handler
        self.prompt_metadata[name] = MCPPrompt(name=name, description=description, arguments=arguments)

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP JSON-RPC request"""
        try:
            # Parse the request
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")

            # Handle different MCP methods
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "resources/list":
                result = await self._handle_list_resources(params)
            elif method == "resources/read":
                result = await self._handle_read_resource(params)
            elif method == "tools/list":
                result = await self._handle_list_tools(params)
            elif method == "tools/call":
                result = await self._handle_call_tool(params)
            elif method == "prompts/list":
                result = await self._handle_list_prompts(params)
            elif method == "prompts/get":
                result = await self._handle_get_prompt(params)
            else:
                raise MCPError(-32601, f"Method not found: {method}")

            # Return successful response
            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        except MCPError as e:
            return {"jsonrpc": "2.0", "id": request_data.get("id"), "error": {"code": e.code, "message": e.message, "data": e.data}}
        except Exception as e:
            logger.exception("Error handling MCP request")
            return {"jsonrpc": "2.0", "id": request_data.get("id"), "error": {"code": -32603, "message": "Internal error", "data": str(e)}}

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"resources": {"subscribe": False, "listChanged": False}, "tools": {}, "prompts": {}},
            "serverInfo": self.server_info,
        }

    async def _handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources = []
        for uri, metadata in self.resource_metadata.items():
            resources.append(asdict(metadata))
        return {"resources": resources}

    def _match_uri_template(self, requested_uri: str) -> Optional[Tuple[str, Dict[str, str]]]:
        """Match requested URI against registered URI templates"""
        for template_uri in self.resources.keys():
            # Extract parameter names from template
            param_names = _extract_uri_params(template_uri)

            if not param_names:
                # Exact match for non-templated URIs
                if requested_uri == template_uri:
                    return template_uri, {}
                continue

            # Create regex pattern from template
            pattern = template_uri
            for param_name in param_names:
                # Use (.+) to match any characters including slashes for paths
                # Use ([^/]+) for single segments
                if param_name in ["path", "file_path", "directory"]:
                    pattern = pattern.replace(f"{{{param_name}}}", r"(.+)")
                else:
                    pattern = pattern.replace(f"{{{param_name}}}", r"([^/]+)")

            match = re.match(f"^{pattern}$", requested_uri)
            if match:
                # Extract parameter values
                param_values = {}
                for i, param_name in enumerate(param_names):
                    param_values[param_name] = match.group(i + 1)
                return template_uri, param_values

        return None

    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")
        if not uri:
            raise MCPError(-32602, "URI is required")

        # Try to match URI template
        match_result = self._match_uri_template(uri)
        if not match_result:
            raise MCPError(-32602, f"Resource not found: {uri}")

        template_uri, uri_params = match_result
        handler = self.resources[template_uri]

        # Call the handler with appropriate parameters based on its signature
        try:
            sig = inspect.signature(handler)
            handler_params = list(sig.parameters.keys())

            if asyncio.iscoroutinefunction(handler):
                if uri_params:
                    # Use URI parameters for templated resources
                    content = await handler(**uri_params)
                elif handler_params:
                    # Handler expects parameters, pass the full params dict
                    content = await handler(params)
                else:
                    # Handler expects no parameters
                    content = await handler()
            else:
                if uri_params:
                    # Use URI parameters for templated resources
                    content = handler(**uri_params)
                elif handler_params:
                    # Handler expects parameters, pass the full params dict
                    content = handler(params)
                else:
                    # Handler expects no parameters
                    content = handler()
        except TypeError as e:
            # Handle parameter mismatch errors
            raise MCPError(-32603, f"Handler parameter error: {str(e)}")

        # Determine content type
        metadata = self.resource_metadata[template_uri]
        mime_type = metadata.mimeType or "text/plain"

        return {"contents": [{"uri": uri, "mimeType": mime_type, "text": str(content)}]}

    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools = []
        for name, metadata in self.tool_metadata.items():
            tools.append(asdict(metadata))
        return {"tools": tools}

    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if not name or name not in self.tools:
            raise MCPError(-32602, f"Tool not found: {name}")

        handler = self.tools[name]

        # Call the tool handler
        if asyncio.iscoroutinefunction(handler):
            result = await handler(**arguments)
        else:
            result = handler(**arguments)

        return {"content": [{"type": "text", "text": str(result)}]}

    async def _handle_list_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request"""
        prompts = []
        for name, metadata in self.prompt_metadata.items():
            prompts.append(asdict(metadata))
        return {"prompts": prompts}

    async def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request"""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if not name or name not in self.prompts:
            raise MCPError(-32602, f"Prompt not found: {name}")

        handler = self.prompts[name]

        # Call the prompt handler
        if asyncio.iscoroutinefunction(handler):
            result = await handler(**arguments)
        else:
            result = handler(**arguments)

        # Ensure result is in the expected format
        if isinstance(result, str):
            messages = [{"role": "user", "content": {"type": "text", "text": result}}]
        elif isinstance(result, list):
            messages = result
        else:
            messages = [{"role": "user", "content": {"type": "text", "text": str(result)}}]

        return {"description": self.prompt_metadata[name].description, "messages": messages}


class MCPApp:
    """MCP application wrapper for Robyn"""

    def __init__(self, robyn_app):
        self.app = robyn_app
        self.handler = MCPHandler()
        self._setup_routes()

    def _setup_routes(self):
        """Setup MCP routes on the Robyn app"""

        @self.app.post("/mcp")
        async def handle_mcp_request(request):
            """Handle MCP JSON-RPC requests"""
            try:
                # Parse JSON request - try multiple approaches
                try:
                    request_data = request.json()
                except (ValueError, TypeError, AttributeError):
                    # Fallback to parsing body as string
                    body = request.body
                    if isinstance(body, str):
                        request_data = json.loads(body)
                    else:
                        request_data = json.loads(body.decode("utf-8"))

                # Handle case where request.json() returns a string instead of dict
                if isinstance(request_data, str):
                    request_data = json.loads(request_data)

                # Handle the request
                response = await self.handler.handle_request(request_data)

                return response

            except json.JSONDecodeError:
                return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
            except Exception as e:
                logger.exception("Error in MCP request handler")
                return {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": "Internal error", "data": str(e)}}

    def resource(self, uri: str = None, name: str = None, description: Optional[str] = None, mime_type: Optional[str] = None):
        """
        Decorator to register an MCP resource

        Args:
            uri: Resource URI template (e.g., "echo://{message}")
            name: Human-readable name (auto-generated if not provided)
            description: Resource description (auto-generated if not provided)
            mime_type: MIME type (defaults to "text/plain")

        Example:
            @app.mcp.resource("echo://{message}")
            def echo_resource(message: str) -> str:
                return f"Resource echo: {message}"
        """

        def decorator(func: Callable):
            # Auto-generate metadata if not provided
            actual_uri = uri or f"function://{func.__name__}"
            actual_name = name or func.__name__.replace("_", " ").title()
            actual_description = description or func.__doc__ or f"Resource: {actual_name}"
            actual_mime_type = mime_type or "text/plain"

            self.handler.register_resource(actual_uri, actual_name, func, actual_description, actual_mime_type)
            return func

        return decorator

    def tool(self, name: str = None, description: str = None, input_schema: Dict[str, Any] = None):
        """
        Decorator to register an MCP tool

        Args:
            name: Tool name (defaults to function name)
            description: Tool description (auto-generated if not provided)
            input_schema: JSON schema for inputs (auto-generated if not provided)

        Example:
            @app.mcp.tool()
            def echo_tool(message: str) -> str:
                return f"Tool echo: {message}"
        """

        def decorator(func: Callable):
            # Auto-generate metadata if not provided
            actual_name = name or func.__name__
            actual_description = description or func.__doc__ or f"Tool: {func.__name__}"
            actual_schema = input_schema or _generate_schema_from_function(func)

            self.handler.register_tool(actual_name, func, actual_description, actual_schema)
            return func

        return decorator

    def prompt(self, name: str = None, description: str = None, arguments: Optional[List[Dict[str, Any]]] = None):
        """
        Decorator to register an MCP prompt

        Args:
            name: Prompt name (defaults to function name)
            description: Prompt description (auto-generated if not provided)
            arguments: Prompt arguments (auto-generated if not provided)

        Example:
            @app.mcp.prompt()
            def echo_prompt(message: str) -> str:
                return f"Please process this message: {message}"
        """

        def decorator(func: Callable):
            # Auto-generate metadata if not provided
            actual_name = name or func.__name__
            actual_description = description or func.__doc__ or f"Prompt: {func.__name__}"
            actual_arguments = arguments or _generate_prompt_args_from_function(func)

            self.handler.register_prompt(actual_name, func, actual_description, actual_arguments)
            return func

        return decorator
