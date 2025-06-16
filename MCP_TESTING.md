# Testing Robyn's MCP Implementation

This document explains how to test the MCP (Model Context Protocol) implementation in Robyn.

## Test Structure

The testing strategy covers three levels:

### 1. 🧪 **Unit Tests** (`test_mcp_manual.py`)
Tests individual components without external dependencies:

- **URI Template Utilities**: Parameter extraction and regex pattern matching
- **Schema Generation**: Auto-generation from Python function signatures  
- **MCP Handler**: Core protocol logic and message handling
- **JSON-RPC Compliance**: Request/response format validation
- **Error Handling**: Proper error codes and messages
- **App Integration**: Decorator syntax and registration

### 2. 🌐 **Live Integration Tests** (`test_mcp_live.py`)
Tests against a real running MCP server:

- **Protocol Compliance**: Full JSON-RPC 2.0 workflow
- **HTTP Transport**: Actual network requests to `/mcp` endpoint
- **Real Server**: Tests with Robyn app serving MCP
- **End-to-End**: Complete client→server→response cycle

### 3. 📋 **Example Validation** 
Validates syntax and imports of example files:

- **Knowledge Assistant**: Production-ready example
- **Simple MCP Server**: Basic demonstration
- **Syntax Checking**: Ensures examples are valid Python

## Running Tests

### Quick Test (Unit Only)
```bash
python run_mcp_tests.py --quick
```

### Full Test Suite
```bash
python run_mcp_tests.py
```

### Live Tests Only
```bash
python run_mcp_tests.py --live-only
```

### Manual Unit Tests
```bash
python test_mcp_manual.py
```

### Manual Live Tests
```bash
# Start server
python test_mcp_live.py start-server

# In another terminal, run tests
python test_mcp_live.py test

# Or run everything at once
python test_mcp_live.py full
```

## Test Coverage

### Core Protocol Features ✅
- [x] JSON-RPC 2.0 message format
- [x] Initialize handshake
- [x] Resources (list, read)
- [x] Tools (list, call)
- [x] Prompts (list, get)
- [x] Error handling (-32601, -32602, -32603)

### URI Template System ✅
- [x] Parameter extraction (`{param}`)
- [x] Path parameters (`{path}` allows slashes)
- [x] Single segment parameters (`{id}` no slashes)
- [x] Multiple parameters (`{op}/{a}/{b}`)
- [x] Template matching and validation

### Auto-Generated Schemas ✅
- [x] Function signature analysis
- [x] Type annotation support (`str`, `int`, `bool`, `float`)
- [x] Required vs optional parameters
- [x] Default value handling
- [x] JSON Schema format compliance

### Decorator Integration ✅
- [x] `@app.mcp.resource()` simplified syntax
- [x] `@app.mcp.tool()` with auto-schemas
- [x] `@app.mcp.prompt()` with auto-arguments
- [x] Custom parameter overrides
- [x] Docstring integration

### Error Scenarios ✅
- [x] Unknown methods
- [x] Missing resources/tools/prompts
- [x] Invalid parameters
- [x] Malformed JSON-RPC
- [x] URI template mismatches

### Real-World Patterns ✅
- [x] File system access (`fs://{path}`)
- [x] Git repository info (`git://repo/{name}`)
- [x] System monitoring (`system://stats`)
- [x] Note creation tools
- [x] Search functionality
- [x] Code analysis prompts

## Test Output Examples

### Successful Unit Test Run
```
🧪 Starting MCP Implementation Tests
============================================================
🧪 Running URI Parameter Extraction... ✅ PASSED
🧪 Running Schema Generation... ✅ PASSED
🧪 Running MCP Handler Basic... ✅ PASSED
🧪 Running JSON-RPC Message Handling... ✅ PASSED
🧪 Running URI Template Matching... ✅ PASSED
🧪 Running MCP App Integration... ✅ PASSED
🧪 Running Error Handling... ✅ PASSED
🧪 Running Knowledge Assistant Patterns... ✅ PASSED
🧪 Running End-to-End Workflow... ✅ PASSED

🎉 ALL TESTS PASSED!
```

### Successful Live Test Run
```
🧪 Testing MCP Protocol Compliance
📋 Testing initialize... ✅ Initialize successful
📋 Testing resources/list... ✅ Found 2 resources
📋 Testing resources/read... ✅ Resource read successful
📋 Testing tools/list... ✅ Found 2 tools
📋 Testing tools/call... ✅ Tool call successful
📋 Testing prompts/list... ✅ Found 1 prompts
📋 Testing prompts/get... ✅ Prompt generation successful

🎉 ALL TESTS PASSED!
```

## Debugging Test Failures

### Common Issues

1. **URI Template Matching Fails**
   - Check parameter names in special list (`path`, `file_path`, `directory`)
   - Verify regex pattern generation
   - Test with simpler URIs first

2. **Schema Generation Issues**
   - Ensure proper type annotations
   - Check function signature parsing
   - Verify required vs optional detection

3. **JSON-RPC Errors**
   - Validate message format
   - Check method names and parameters
   - Verify error code handling

4. **Live Test Connection Issues**
   - Ensure no other process on port 8080
   - Check server startup logs
   - Verify health endpoint responds

### Debugging Flags

Add debug output by modifying test files:
```python
# In test_mcp_manual.py
print(f"DEBUG: {variable_name}")

# In MCP handler
logger.debug(f"Processing request: {request}")
```

## Test Data

Tests use these sample patterns:

### Resources
- `echo://{message}` - Simple echo
- `fs://{path}` - File system access
- `git://repo/{repo_name}` - Git repository
- `system://stats` - Static system info

### Tools
- `calculate(expression: str)` - Math evaluation
- `greet(name: str, formal: bool = False)` - Greeting generation

### Prompts
- `explain_code(code: str, language: str = "python")` - Code explanation
- `analyze_file(file_path: str)` - File analysis

## Performance Considerations

Tests are designed to be fast:
- Unit tests: ~2-3 seconds
- Live tests: ~10-15 seconds (includes server startup)
- No external dependencies required
- Parallel test execution where possible

## Continuous Integration

For CI/CD pipelines:
```bash
# Quick validation (for PR checks)
python run_mcp_tests.py --quick

# Full validation (for releases)
python run_mcp_tests.py
```

The test suite returns proper exit codes:
- `0` = All tests passed
- `1` = Some tests failed

## Adding New Tests

To add new test cases:

1. **Unit Tests**: Add to `test_mcp_manual.py`
2. **Live Tests**: Add to `test_mcp_live.py`
3. **Examples**: Add validation to `run_mcp_tests.py`

Follow the existing patterns and ensure tests are:
- Independent (no shared state)
- Deterministic (same result every time)
- Fast (complete in seconds)
- Clear (obvious what they're testing)