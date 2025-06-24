#!/usr/bin/env python3
"""
Robyn MCP Server Example

Simple MCP server demonstrating basic resources and tools.
Run with: python examples/mcp.py
"""

import json
import platform
from datetime import datetime

from robyn import Robyn

app = Robyn(__file__)


# MCP Resources
@app.mcp.resource("time://current")
def current_time() -> str:
    return f"Current time: {datetime.now().isoformat()}"


@app.mcp.resource("system://info")
def system_info() -> str:
    return json.dumps({"platform": platform.system(), "python_version": platform.python_version(), "timestamp": datetime.now().isoformat()})


# MCP Tools
@app.mcp.tool(
    name="calculate",
    description="Perform safe mathematical calculations",
    input_schema={
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "Math expression like '2 + 2'"}},
        "required": ["expression"],
    },
)
def calculate_tool(args):
    expression = args.get("expression", "")
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        return "Error: Invalid characters in expression"

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@app.mcp.tool(
    name="echo",
    description="Echo back text",
    input_schema={"type": "object", "properties": {"text": {"type": "string", "description": "Text to echo"}}, "required": ["text"]},
)
def echo_tool(args):
    return args.get("text", "")


# MCP Prompts
@app.mcp.prompt(
    name="explain_code",
    description="Generate code explanation prompt",
    arguments=[
        {"name": "code", "description": "Code to explain", "required": True},
        {"name": "language", "description": "Programming language", "required": False},
    ],
)
def explain_code_prompt(args):
    code = args.get("code", "")
    language = args.get("language", "unknown")

    return f"""Please explain this {language} code:

```{language}
{code}
```

Include:
1. What it does
2. How it works
3. Key concepts used
"""


@app.get("/")
def home():
    return {
        "name": "Robyn MCP Server Example",
        "mcp_endpoint": "/mcp",
        "resources": ["time://current", "system://info"],
        "tools": ["calculate", "echo"],
        "prompts": ["explain_code"],
    }


if __name__ == "__main__":
    print("Robyn MCP Server Example")
    print(f"Server: http://localhost:8080")
    print(f"MCP Endpoint: http://localhost:8080/mcp")
    app.start(port=8080)
