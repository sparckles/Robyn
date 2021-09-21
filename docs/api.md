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



## Returning a JSON Response
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

To see a complete service in action, you can go to the folder [../test_python/test.py](../test_python/test.py)
