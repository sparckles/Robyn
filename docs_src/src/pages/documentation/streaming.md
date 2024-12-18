# Streaming Responses in Robyn

Robyn supports streaming responses for various use cases including real-time data, large file downloads, and server-sent events (SSE). This document explains how to use streaming responses effectively.

## Basic Usage

There are two ways to create streaming responses in Robyn:

1. Using the `streaming` parameter in route decorators:
```python
@app.get("/stream", streaming=True)
async def stream():
    async def generator():
        for i in range(5):
            yield f"Chunk {i}\n".encode()
    
    return Response(
        status_code=200,
        headers={"Content-Type": "text/plain"},
        description=generator()
    )
```

2. Returning an iterator/generator directly:
```python
@app.get("/stream")
async def stream():
    async def generator():
        for i in range(5):
            yield f"Chunk {i}\n".encode()
    
    return generator()  # Robyn will automatically detect this as a streaming response
```

## Supported Types

Robyn's streaming response system supports multiple data types:

1. **Binary Data** (`bytes`)
```python
async def generator():
    yield b"Binary data"
```

2. **Text Data** (`str`)
```python
async def generator():
    yield "String data".encode()  # Must be encoded
```

3. **Numbers** (`int`, `float`)
```python
async def generator():
    yield str(42).encode()  # Must be converted to string and encoded
```

4. **JSON Data**
```python
async def generator():
    import json
    data = {"key": "value"}
    yield json.dumps(data).encode()
```

## Use Cases

### 1. Server-Sent Events (SSE)

SSE allows real-time updates from server to client:

```python
@app.get("/events", streaming=True)
async def sse():
    async def event_generator():
        while True:
            data = {"time": time.time(), "event": "update"}
            yield f"data: {json.dumps(data)}\n\n".encode()
            await asyncio.sleep(1)
    
    return Response(
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        },
        description=event_generator()
    )
```

Client usage:
```javascript
const evtSource = new EventSource("/events");
evtSource.onmessage = (event) => {
    console.log(JSON.parse(event.data));
};
```

### 2. Large File Downloads

Stream large files in chunks to manage memory usage:

```python
@app.get("/download", streaming=True)
async def download():
    async def file_generator():
        chunk_size = 8192  # 8KB chunks
        with open("large_file.bin", "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk
    
    return Response(
        status_code=200,
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Disposition": "attachment; filename=file.bin"
        },
        description=file_generator()
    )
```

### 3. CSV Generation

Stream CSV data as it's generated:

```python
@app.get("/csv", streaming=True)
async def csv():
    async def csv_generator():
        # Write headers
        yield "id,name,value\n".encode()
        
        # Stream data rows
        for i in range(1000):
            row = f"{i},item-{i},{random.randint(1,100)}\n"
            yield row.encode()
            await asyncio.sleep(0.01)  # Simulate processing time
    
    return Response(
        status_code=200,
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=data.csv"
        },
        description=csv_generator()
    )
```

## Best Practices

1. **Always encode your data**
   ```python
   # Wrong
   yield "data"  # Will fail
   # Correct
   yield "data".encode()
   ```

2. **Set appropriate headers**
   ```python
   # For SSE
   headers = {
       "Content-Type": "text/event-stream",
       "Cache-Control": "no-cache",
       "Connection": "keep-alive"
   }
   
   # For file downloads
   headers = {
       "Content-Type": "application/octet-stream",
       "Content-Disposition": "attachment; filename=file.dat"
   }
   ```

3. **Handle errors gracefully**
   ```python
   async def generator():
       try:
           for item in items:
               yield process(item)
       except Exception as e:
           yield f"Error: {str(e)}".encode()
           return
   ```

4. **Memory management**
   ```python
   # Wrong - accumulates all data in memory
   data = []
   async def generator():
       for i in range(1000000):
           data.append(i)  # Memory leak
           yield str(i).encode()
   
   # Correct - streams data directly
   async def generator():
       for i in range(1000000):
           yield str(i).encode()
   ```

## Testing

Test streaming responses using aiohttp:

```python
@pytest.mark.asyncio
async def test_stream():
    async with aiohttp.ClientSession() as client:
        async with client.get("http://localhost:8080/stream") as response:
            chunks = []
            async for chunk in response.content:
                chunks.append(chunk.decode())
            assert len(chunks) > 0
```

## Common Issues

1. **Not encoding data**
   ```python
   # Wrong
   yield "data"  # Will fail
   # Correct
   yield "data".encode()
   ```

2. **Not setting correct headers**
   ```python
   # SSE needs specific headers
   headers = {
       "Content-Type": "text/event-stream",
       "Cache-Control": "no-cache",
       "Connection": "keep-alive"
   }
   ```

3. **Memory leaks**
   ```python
   # Wrong
   data = []
   async def generator():
       for i in range(1000000):
           data.append(i)  # Memory leak
           yield str(i).encode()
   
   # Correct
   async def generator():
       for i in range(1000000):
           yield str(i).encode()
   ```

## Performance Considerations

1. Use appropriate chunk sizes (typically 8KB-64KB)
2. Implement backpressure handling
3. Consider using async file I/O for large files
4. Monitor memory usage during streaming
5. Implement timeouts for long-running streams

## Helper Functions

Robyn provides helper functions for common streaming scenarios:

```python
from robyn import Response, html

# Stream HTML content
@app.get("/stream-html", streaming=True)
async def stream_html():
    async def generator():
        yield "<html><body>"
        for i in range(5):
            yield f"<p>Chunk {i}</p>"
            await asyncio.sleep(0.1)
        yield "</body></html>"
    
    return html(generator(), streaming=True)
```

## What's Next?

Now that you've mastered streaming responses, you might want to explore:

- [WebSockets](/documentation/api_reference/websockets) for real-time bidirectional communication
- [File Handling](/documentation/api_reference/file_handling) for more file operations
- [Middleware](/documentation/api_reference/middleware) for request/response processing