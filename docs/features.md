## Features


## Synchronous Requests
Robyn supports both sync methods and async methods for fetching requests. Every method gets a request object from the routing decorator.

```python

@app.get("/")
def h(request):
    return "Hello, world"
```

## Async Requests

```python
@app.get("/")
async def h(request):
    return "Hello, world"
```


## All kinds of HTTP Requests

The request object contains the `body` in PUT/POST/PATCH. The `header`s are available in every request object.

Robyn supports every HTTP request method. The examples of some of them are below:

#### GET Request

```python
@app.get("/")
async def h(request):
    return "Hello World"
```

#### POST Request

```python
@app.post("/post")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")
```

#### PUT Request

```python
@app.put("/put")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")
```


#### PATCH Request

```python
@app.patch("/patch")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")
```


#### DELETE Request

```python
@app.delete("/delete")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")
```


#### Directory Serving

```python
app.add_directory(
    route="/test_dir"
    directory_path="/build"
    index_file="index.html"
)
```

## Dynamic Routes
You can add params in the routes and access them from the request object.

```python
@app.post("/jsonify/:id")
async def json(request):
    print(request["params"]["id"])
    return jsonify({"hello": "world"})
```

## Returning a JSON Response
You can also serve JSON responses when serving HTTP request using the following way.

```python
from robyn import jsonify

@app.post("/jsonify")
async def json(request):
    print(request)
    return jsonify({"hello": "world"})
```

## Global Headers
You can also add global headers for every request.

```python
app.add_header("server", "robyn")

```


## Query Params

You can access query params from every HTTP method.

For the url: `http://localhost:5000/query?a=b`

You can use the following code snippet.

```python
@app.get("/query")
async def query_get(request):
    query_data = request["queries"]
    return jsonify(query_data)
```


## Events

You can add startup and shutdown events in robyn. These events will execute before the requests have started serving and after the serving has been completed.

```python

async def startup_handler():
    print("Starting up")

app.startup_handler(startup_handler)

@app.shutdown_handler
def shutdown_handler():
    print("Shutting down")
```

## WebSockets

You can now serve websockets using Robyn.

Firstly, you need to create a WebSocket Class and wrap it around your Robyn app.

```python
from robyn import Robyn, static_file, jsonify, WS


app = Robyn(__file__)
websocket = WS(app, "/web_socket")
```

Now, you can define 3 methods for every web_socket for their life cycle, they are as follows:

```python
@websocket.on("message")
def connect():
    global i
    i+=1
    if i==0:
        return "Whaaat??"
    elif i==1:
        return "Whooo??"
    elif i==2:
        return "*chika* *chika* Slim Shady."
    elif i==3:
        i= -1
        return ""

@websocket.on("close")
def close():
    return "Goodbye world, from ws"

@websocket.on("connect")
def message():
    return "Hello world, from ws"

```

The three methods:
 - "message" is called when the socket receives a message
 - "close" is called when the socket is disconnected
 - "connect" is called when the socket connects

To see a complete service in action, you can go to the folder [../integration_tests/base_routes.py](../integration_tests/base_routes.py)


#### Web Socket Usage

```python
@websocket.on("message")
async def connect():
    global i
    i+=1
    if i==0:
        return "Whaaat??"
    elif i==1:
        return "Whooo??"
    elif i==2:
        return "*chika* *chika* Slim Shady."
    elif i==3:
        i= -1
        return ""

@websocket.on("close")
async def close():
    return "Goodbye world, from ws"

@websocket.on("connect")
async def message():
    return "Hello world, from ws"

```

## Middlewares

You can use both sync and async functions for middlewares!

```python
@app.before_request("/")
async def hello_before_request(request):
    print(request)


@app.after_request("/")
def hello_after_request(request):
    print(request)
```

## MultiCore Scaling

To run Robyn across multiple cores, you can use the following command:

`python app.py --workers=N --processes=N`



## Const Requests

You can pre-compute the response for each route. This will compute the response even before execution. This will improve the response time bypassing the need to access the router.

```python
@app.get("/", const=True)
async def h():
    return "Hello, world"
```

