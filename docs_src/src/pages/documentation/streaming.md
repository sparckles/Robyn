# Streaming Responses in Robyn

Robyn supports streaming responses for various use cases including real-time data, large file downloads, and server-sent events (SSE). This document explains how to use streaming responses effectively.

## Basic Usage

### Simple Streaming Response

```python
@app.get("/stream")
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

## Supported Types

Robyn's streaming response system supports multiple data types:

1. **Binary Data** (`bytes`)
```python
yield b"Binary data"
```

2. **Text Data** (`str`)
```python
yield "String data".encode()
```

3. **Numbers** (`int`, `float`)
```python
yield str(42).encode()
```

4. **JSON Data**
```python
import json
data = {"key": "value"}
yield json.dumps(data).encode()
```

## Use Cases

### 1. Server-Sent Events (SSE)

SSE allows real-time updates from server to client:

```python
@app.get("/events")
async def sse():
    async def event_generator():
        yield f"event: message\ndata: {json.dumps(data)}\n\n".encode()
        
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
@app.get("/download")
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
@app.get("/csv")
async def csv():
    async def csv_generator():
        yield "header1,header2\n".encode()
        for item in data:
            yield f"{item.field1},{item.field2}\n".encode()
    
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
   - Convert strings to bytes using `.encode()`
   - Use `json.dumps().encode()` for JSON data

2. **Set appropriate headers**
   - Use correct Content-Type
   - Add Content-Disposition for downloads
   - Set Cache-Control for SSE

3. **Handle errors gracefully**
   ```python
   async def generator():
       try:
           for item in items:
               yield process(item)
       except Exception as e:
           yield f"Error: {str(e)}".encode()
   ```

4. **Memory management**
   - Use appropriate chunk sizes
   - Don't hold entire dataset in memory
   - Clean up resources after streaming

## Testing

Test streaming responses using the test client:

```python
@pytest.mark.asyncio
async def test_stream():
    async with app.test_client() as client:
        response = await client.get("/stream")
        chunks = []
        async for chunk in response.content:
            chunks.append(chunk)
        # Assert on chunks
```

## Common Issues

1. **Forgetting to encode data**
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