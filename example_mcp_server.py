#!/usr/bin/env python3
"""
Example MCP (Model Context Protocol) server using Robyn.

This demonstrates how to create an MCP server that exposes resources, tools, and prompts
to MCP clients like Claude Desktop or other AI applications.

To test this server:
1. Run: python example_mcp_server.py
2. The MCP endpoint will be available at: http://localhost:8080/mcp
3. Send JSON-RPC 2.0 requests to test the functionality

Example MCP client requests:

# Initialize connection
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}}}'

# List available resources
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}}'

# Read a resource
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "system://time"}}'

# List available tools
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}}'

# Call a tool
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "calculate", "arguments": {"expression": "2 + 2"}}}'
"""

import json
import os
import time
from datetime import datetime
from robyn import Robyn

# Initialize the Robyn app
app = Robyn(__file__)

# Example: Register MCP resources
@app.mcp.resource(
    uri="system://time",
    name="System Time",
    description="Get current system time and date",
    mime_type="text/plain"
)
def get_system_time(params):
    """Return current system time"""
    return f"Current time: {datetime.now().isoformat()}"

@app.mcp.resource(
    uri="system://info",
    name="System Info", 
    description="Get basic system information",
    mime_type="application/json"
)
def get_system_info(params):
    """Return system information"""
    return json.dumps({
        "platform": os.name,
        "cwd": os.getcwd(),
        "pid": os.getpid(),
        "env_vars": len(os.environ)
    })

@app.mcp.resource(
    uri="file://readme",
    name="README",
    description="Application README information",
    mime_type="text/markdown"
)
def get_readme(params):
    """Return README content"""
    return """# MCP Server Example

This is a demonstration of Robyn's MCP (Model Context Protocol) support.

## Features
- Resources: Access to system information and files
- Tools: Executable functions for calculations and utilities  
- Prompts: Template-based message generation

## Usage
Connect using any MCP client to interact with this server.
"""

# Example: Register MCP tools
@app.mcp.tool(
    name="calculate",
    description="Perform basic mathematical calculations",
    input_schema={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
            }
        },
        "required": ["expression"]
    }
)
def calculate_tool(args):
    """Safe calculator tool"""
    expression = args.get("expression", "")
    
    # Basic safety check - only allow safe characters
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        return "Error: Expression contains invalid characters"
    
    try:
        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error: Could not evaluate '{expression}' - {str(e)}"

@app.mcp.tool(
    name="echo",
    description="Echo back the provided text",
    input_schema={
        "type": "object", 
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to echo back"
            }
        },
        "required": ["text"]
    }
)
def echo_tool(args):
    """Simple echo tool"""
    text = args.get("text", "")
    return f"Echo: {text}"

@app.mcp.tool(
    name="timestamp",
    description="Get current timestamp in various formats",
    input_schema={
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "Format type: 'iso', 'unix', or 'human'",
                "enum": ["iso", "unix", "human"]
            }
        }
    }
)
def timestamp_tool(args):
    """Get timestamp in different formats"""
    format_type = args.get("format", "iso")
    now = datetime.now()
    
    if format_type == "unix":
        return f"Unix timestamp: {int(now.timestamp())}"
    elif format_type == "human":
        return f"Human readable: {now.strftime('%Y-%m-%d %H:%M:%S')}"  
    else:  # iso
        return f"ISO format: {now.isoformat()}"

# Example: Register MCP prompts
@app.mcp.prompt(
    name="explain_code",
    description="Generate a prompt for explaining code",
    arguments=[
        {
            "name": "code", 
            "description": "The code to explain",
            "required": True
        },
        {
            "name": "language",
            "description": "Programming language",
            "required": False
        }
    ]
)
def explain_code_prompt(args):
    """Generate code explanation prompt"""
    code = args.get("code", "")
    language = args.get("language", "unknown")
    
    prompt = f"""Please explain the following {language} code:

```{language}
{code}
```

Provide a clear explanation that covers:
1. What the code does
2. How it works
3. Any important concepts or patterns used
4. Potential improvements or concerns
"""
    
    return [
        {
            "role": "user",
            "content": {
                "type": "text", 
                "text": prompt
            }
        }
    ]

@app.mcp.prompt(
    name="debug_help",
    description="Generate a prompt for debugging assistance",
    arguments=[
        {
            "name": "error_message",
            "description": "The error message encountered", 
            "required": True
        },
        {
            "name": "context",
            "description": "Additional context about the error",
            "required": False
        }
    ]
)
def debug_help_prompt(args):
    """Generate debugging assistance prompt"""
    error_message = args.get("error_message", "")
    context = args.get("context", "")
    
    prompt = f"""I'm encountering the following error:

Error: {error_message}

{f"Context: {context}" if context else ""}

Can you help me understand:
1. What this error means
2. Common causes of this error
3. Steps to debug and fix it
4. How to prevent similar errors in the future
"""
    
    return prompt

# Regular Robyn routes
@app.get("/")
def home():
    """Home page with MCP server information"""  
    return {
        "message": "Robyn MCP Server",
        "description": "Model Context Protocol server implementation",
        "mcp_endpoint": "/mcp",
        "capabilities": {
            "resources": ["system://time", "system://info", "file://readme"],
            "tools": ["calculate", "echo", "timestamp"],
            "prompts": ["explain_code", "debug_help"]
        },
        "usage": "Send JSON-RPC 2.0 requests to /mcp endpoint"
    }

@app.get("/status")
def status():
    """Server status endpoint"""
    return {
        "status": "running",
        "server": "robyn-mcp-server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🤖 Starting Robyn MCP Server")
    print("=" * 40)
    print(f"🌐 Server: http://localhost:8080")
    print(f"🔌 MCP Endpoint: http://localhost:8080/mcp")
    print(f"📚 Info: http://localhost:8080")
    print(f"💚 Status: http://localhost:8080/status")
    print()
    print("MCP Capabilities:")
    print("  📁 Resources: system://time, system://info, file://readme")  
    print("  🔧 Tools: calculate, echo, timestamp")
    print("  💭 Prompts: explain_code, debug_help")
    print()
    print("Example MCP request:")
    print("  curl -X POST http://localhost:8080/mcp \\")
    print("    -H 'Content-Type: application/json' \\") 
    print("    -d '{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"initialize\", \"params\": {}}'")
    print()
    
    app.start(port=8080)