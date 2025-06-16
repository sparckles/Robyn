#!/usr/bin/env python3
"""
Simple MCP (Model Context Protocol) server example using the new simplified decorator syntax.

This demonstrates the clean decorator syntax that auto-generates schemas and metadata.
"""

from robyn import Robyn

app = Robyn(__file__)

# Resource with URI template - parameters extracted automatically
@app.mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"

@app.mcp.resource("user://{user_id}/profile")  
def user_profile(user_id: str) -> str:
    """Get user profile information"""
    return f"User {user_id} profile data: {'name': 'John Doe', 'email': 'john@example.com'}"

@app.mcp.resource("math://{operation}/{a}/{b}")
def math_resource(operation: str, a: str, b: str) -> str:
    """Perform mathematical operations"""
    try:
        num_a, num_b = float(a), float(b)
        if operation == "add":
            result = num_a + num_b
        elif operation == "subtract": 
            result = num_a - num_b
        elif operation == "multiply":
            result = num_a * num_b
        elif operation == "divide":
            result = num_a / num_b if num_b != 0 else "Error: Division by zero"
        else:
            result = f"Unknown operation: {operation}"
        return f"{operation}({a}, {b}) = {result}"
    except ValueError:
        return f"Error: Invalid numbers {a}, {b}"

# Tools with auto-generated schemas
@app.mcp.tool()
def echo_tool(message: str) -> str:
    """Echo a message back to the user"""
    return f"Tool echo: {message}"

@app.mcp.tool()
def calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions"""
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        return "Error: Expression contains invalid characters"
    
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"

@app.mcp.tool()
def greet(name: str, formal: bool = False) -> str:
    """Generate a greeting message"""
    if formal:
        return f"Good day, {name}. How may I assist you?"
    else:
        return f"Hey {name}! What's up?"

# Prompts with auto-generated arguments
@app.mcp.prompt()
def echo_prompt(message: str) -> str:
    """Generate a prompt that asks the AI to process a message"""
    return f"Please process this message: {message}"

@app.mcp.prompt()
def code_review(code: str, language: str = "python") -> str:
    """Generate a code review prompt"""
    return f"""Please review this {language} code and provide feedback:

```{language}
{code}
```

Focus on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance improvements
4. Readability and maintainability"""

@app.mcp.prompt()
def explain_concept(topic: str, audience: str = "general") -> str:
    """Generate a prompt to explain a concept to a specific audience"""
    return f"Explain the concept of '{topic}' for a {audience} audience. Be clear and use appropriate examples."

# Regular Robyn routes for testing
@app.get("/")
def home():
    return {
        "message": "Simple MCP Server with Auto-Generated Schemas",
        "features": [
            "URI template support with parameter extraction",
            "Auto-generated JSON schemas from function signatures", 
            "Simplified decorator syntax",
            "Type-aware parameter handling"
        ],
        "mcp_endpoint": "/mcp",
        "examples": {
            "resources": [
                "echo://hello",
                "user://123/profile", 
                "math://add/10/5"
            ],
            "tools": ["echo_tool", "calculate", "greet"],
            "prompts": ["echo_prompt", "code_review", "explain_concept"]
        }
    }

@app.get("/test")
async def test_mcp():
    """Test the MCP functionality"""
    # Get the MCP handler for testing
    mcp_handler = app.mcp.handler
    
    # Test resource matching
    match_result = mcp_handler._match_uri_template("echo://hello")
    
    results = {
        "uri_template_test": {
            "requested": "echo://hello",
            "matched": match_result is not None,
            "template": match_result[0] if match_result else None,
            "params": match_result[1] if match_result else None
        },
        "registered_resources": list(mcp_handler.resource_metadata.keys()),
        "registered_tools": list(mcp_handler.tool_metadata.keys()),
        "registered_prompts": list(mcp_handler.prompt_metadata.keys())
    }
    
    return results

if __name__ == "__main__":
    print("🚀 Simple MCP Server with Auto-Generated Schemas")
    print("=" * 50)
    print(f"🌐 Server: http://localhost:8080")
    print(f"🔌 MCP Endpoint: http://localhost:8080/mcp")
    print(f"🧪 Test: http://localhost:8080/test")
    print()
    print("Resource URI Templates:")
    print("  echo://{message}")
    print("  user://{user_id}/profile")
    print("  math://{operation}/{a}/{b}")
    print()
    print("Example MCP requests:")
    print("  # Read echo resource")
    print("  curl -X POST http://localhost:8080/mcp \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"resources/read\", \"params\": {\"uri\": \"echo://hello\"}}'")
    print()
    print("  # Call tool")
    print("  curl -X POST http://localhost:8080/mcp \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"jsonrpc\": \"2.0\", \"id\": 2, \"method\": \"tools/call\", \"params\": {\"name\": \"greet\", \"arguments\": {\"name\": \"Alice\", \"formal\": true}}}'")
    print()
    
    app.start(port=8080)