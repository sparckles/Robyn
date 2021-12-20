# API Usage

## Getting Started

```python

from robyn import Robyn

app = Robyn(__file__)

@app.get("/")
async def h():
    return "Hello, world!"

app.start(port=5000, url="0.0.0.0") # url is optional, defaults to 127.0.0.1

```

Let us try to decipher the usage line by line.

> from robyn import Robyn

This statement just imports the Robyn structure from the robyn package.

> app = Robyn(__file__)

Here, we are creating the app object. We require the `__file__` object to mount the directory for hot reloading.

## Running the service

You can just use the command 

```
python3 app.py
```

if you want to run the production version, and

```
python3 app.py --dev=true
```
if you want to enable hot reloading or the development version.

## Serving an HTTP Request


Robyn supports both sync methods and async methods for fetching requests. Every method gets a request object from the routing decorator.

The request object contains the `body` in PUT/POST/PATCH. The `header`s are available in every request object.

Robyn supports every HTTP request method. The examples of some of them are below:
### GET Request

```python3
@app.get("/")
async def h(request):
    return "Hello World"
```

### POST Request

```python3
@app.post("/post")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")
```

### PUT Request

```python3
@app.put("/put")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")
```


### PATCH Request

```python3
@app.patch("/patch")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")
```


### DELETE Request

```python3
@app.delete("/delete")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")
```


### Having Dynamic Routes
You can now add params in the routes and access them from the request object.

```python3
@app.post("/jsonify/:id")
async def json(request):
    print(request["params"]["id"])
    return jsonify({"hello": "world"})
```

### Returning a JSON Response
You can also serve JSON responses when serving HTTP request using the following way.

```python3
from robyn import jsonify

@app.post("/jsonify")
async def json(request):
    print(request)
    return jsonify({"hello": "world"})
```

### Serving a Directory
You can also use robyn to serve a directory. An example use case of this method would be when you want to build and serve a react/vue/angular/vanilla js app.

You would type the following command to generate the build directory.
```
    yarn build
```

and you can then add the following method in your robyn app.

```python3
app.add_directory(route="/react_app_serving",directory_path="./build", index_file="index.html")

```


### Serving a Static File

If you don't want to serve static directory and want to just serve static_files, you can use the following method.
```python3
from robyn import Robyn, static_file

@app.get("/test")
async def test():
    return static_file("index.html")

```

### Serving Headers
You can also add global headers for every request.

```python3
app.add_header("server", "robyn")

```

## WebSockets

You can now serve websockets using Robyn.

Firstly, you need to create a WebSocket Class and wrap it around your Robyn app.

```python3
from robyn import Robyn, static_file, jsonify, WS


app = Robyn(__file__)
websocket = WS(app, "/web_socket")
```

Now, you can define 3 methods for every web_socket for their life cycle, they are as follows:

```python3
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

### Update(20/12/21)

Async functions are supported in Web Sockets now!

Async functions are executed out of order for web sockets. i.e. the order of response is not guaranteed. This is done to achieve a non blocking concurrent effect. 

A blocking async web socket is in plans for the future.

### Usage

```python3
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


## MutliCore Scaling

To run Robyn across multiple cores, you can use the following command:

`python3 app.py --workers=N --processes=N`
