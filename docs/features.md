## Features

### Synchronous API
```python3

@app.get(‘/’)
def h():
    return “Hello, world”
```

### Async API

```python3
@app.get(‘/’)
async def h():
    return “Hello, world”
```

### Directory Serving

```python3
app.add_directory(
    route=”/test_dir”,
    directory_path=”/build”,
    index_file=”index.html”
)
```

### Static File Serving

```python3
from Robyn import static_file

@app.get(‘/’)
async def test():
   return static_file(“./index.html”)
```

### URL Routing

```python3
@app.get("/test/:test_file")
async def test(request):
    test_file = request["params"]["test_file"]
    return static_file("./index.html")
```

### Multi Core Scaling

```python3
python3 app.py \
	--processes=N \
	--workers=N
```

### Middlewares

```python3
@app.before_request("/")
async def hello_before_request(request):
    print(request)
    return ""

@app.after_request("/")
async def hello_after_request(request):
    print(request)
    return ""
```


### WebSockets

```python3
from robyn import WS

websocket = WS(app, "/web_socket")

@websocket.on("message")
async def connect(websocket_id):
    return �how are you�

@websocket.on("close")
def close():
    return "GoodBye world, from ws"

@websocket.on("connect")
async def message():
    return "Hello world, from ws"
```

### Const Requests

```python3
@app.get(‘/’, const=True)
async def h():
    return “Hello, world”
```

