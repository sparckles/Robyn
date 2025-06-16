# MCP (Model Context Protocol) Support in Robyn

Robyn now supports the Model Context Protocol (MCP), allowing your applications to serve as MCP servers that can be connected to by AI applications like Claude Desktop.

## Quick Start

```python
from robyn import Robyn

app = Robyn(__file__)

# Resource with URI template
@app.mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"

# Tool with auto-generated schema
@app.mcp.tool()
def echo_tool(message: str) -> str:
    """Echo a message back to the user"""
    return f"Tool echo: {message}"

# Prompt with auto-generated arguments
@app.mcp.prompt()
def echo_prompt(message: str) -> str:
    """Generate a prompt that asks the AI to process a message"""
    return f"Please process this message: {message}"

app.start()
```

## Features

### 🎯 **Simplified Decorator Syntax**
- Auto-generates JSON schemas from function signatures
- Supports URI templates with parameter extraction
- Minimal boilerplate code

### 🔌 **Full MCP Compliance**
- JSON-RPC 2.0 protocol support
- All standard MCP methods (initialize, resources, tools, prompts)
- Proper error handling and responses

### 🚀 **Type-Aware Parameter Handling**
- Automatic type inference from type annotations
- Support for required and optional parameters
- URI template parameter extraction

## Decorator Reference

### `@app.mcp.resource(uri, name=None, description=None, mime_type=None)`

Register an MCP resource that can be read by clients.

**Parameters:**
- `uri`: Resource URI template (e.g., `"file://{path}"`, `"user://{id}/profile"`)
- `name`: Human-readable name (auto-generated from function name if not provided)
- `description`: Resource description (uses docstring if not provided)
- `mime_type`: MIME type (defaults to `"text/plain"`)

**Examples:**
```python
# Simple resource
@app.mcp.resource("time://current")
def current_time() -> str:
    return datetime.now().isoformat()

# Resource with URI template
@app.mcp.resource("user://{user_id}/profile")
def user_profile(user_id: str) -> str:
    return f"Profile for user {user_id}"

# Resource with multiple parameters
@app.mcp.resource("math://{operation}/{a}/{b}")
def math_operation(operation: str, a: str, b: str) -> str:
    # Implementation here
    pass
```

### `@app.mcp.tool(name=None, description=None, input_schema=None)`

Register an MCP tool that can be executed by AI models.

**Parameters:**
- `name`: Tool name (defaults to function name)
- `description`: Tool description (uses docstring if not provided)
- `input_schema`: JSON schema for inputs (auto-generated if not provided)

**Examples:**
```python
# Simple tool with auto-generated schema
@app.mcp.tool()
def calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions"""
    return str(eval(expression, {"__builtins__": {}}, {}))

# Tool with typed parameters
@app.mcp.tool()
def greet(name: str, formal: bool = False) -> str:
    """Generate a greeting message"""
    if formal:
        return f"Good day, {name}."
    return f"Hi {name}!"

# Tool with custom schema
@app.mcp.tool(input_schema={
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "language": {"type": "string", "enum": ["en", "es", "fr"]}
    },
    "required": ["text"]
})
def translate(text: str, language: str = "en") -> str:
    # Translation implementation
    pass
```

### `@app.mcp.prompt(name=None, description=None, arguments=None)`

Register an MCP prompt template for AI workflows.

**Parameters:**
- `name`: Prompt name (defaults to function name)
- `description`: Prompt description (uses docstring if not provided)
- `arguments`: Prompt arguments (auto-generated if not provided)

**Examples:**
```python
# Simple prompt
@app.mcp.prompt()
def code_review(code: str, language: str = "python") -> str:
    """Generate a code review prompt"""
    return f"Please review this {language} code: {code}"

# Complex prompt with multiple parameters
@app.mcp.prompt()
def debug_help(error: str, context: str = "", language: str = "python") -> str:
    """Generate debugging assistance prompt"""
    prompt = f"I'm getting this error in {language}: {error}"
    if context:
        prompt += f"\n\nContext: {context}"
    prompt += "\n\nCan you help me debug this?"
    return prompt
```

## Type Support

The auto-generated schemas support these Python types:

| Python Type | JSON Schema Type |
|------------|------------------|
| `str` | `"string"` |
| `int` | `"integer"` |
| `float` | `"number"` |
| `bool` | `"boolean"` |
| `List[T]`, `Dict[K,V]` | `"object"` |

## URI Templates

Resources support URI templates with parameter extraction:

```python
@app.mcp.resource("api://{version}/users/{user_id}/posts/{post_id}")
def get_user_post(version: str, user_id: str, post_id: str) -> str:
    return f"Post {post_id} from user {user_id} (API v{version})"
```

When a client requests `"api://v1/users/123/posts/456"`, the function will be called with:
- `version="v1"`
- `user_id="123"`
- `post_id="456"`

## Client Usage

MCP clients communicate via JSON-RPC 2.0 to the `/mcp` endpoint:

```bash
# Initialize connection
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'

# List resources
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}}'

# Read resource
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "echo://hello"}}'

# Call tool
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "calculate", "arguments": {"expression": "2+2"}}}'
```

## Integration with Claude Desktop

To connect your Robyn MCP server to Claude Desktop:

1. Start your Robyn app with MCP endpoints
2. Configure Claude Desktop to connect to `http://localhost:8080/mcp`
3. Use the registered resources, tools, and prompts in your conversations

## Error Handling

The MCP implementation provides proper error responses:

```python
@app.mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Division by zero")
    return str(a / b)
```

Errors are automatically converted to proper MCP error responses.

## Complete Example

See `example_mcp_simple.py` for a complete working example with resources, tools, and prompts.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that enables AI applications to securely connect to external data sources and tools. Think of it as "USB-C for AI" - a standardized way to connect AI models to different resources.

For more information, visit: https://modelcontextprotocol.io/