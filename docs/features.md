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
    return request.body
```

#### PUT Request

```python
@app.put("/put")
async def putreq(request):
    return request.body
```

#### PATCH Request

```python
@app.patch("/patch")
async def patchreq(request):
    return request.body
```

#### DELETE Request

```python
@app.delete("/delete")
async def deletereq(request):
    return request.body
```

#### Directory Serving

```python
app.add_directory(
    route="/test_dir",
    directory_path="build/",
    index_file="index.html",
)
```

## Dynamic Routes

You can add path params in the routes and access them from the request object.

```python
from robyn import jsonify


@app.post("/jsonify/:id")
async def json(request):
    print(request["path_params"]["id"])
    return jsonify({"hello": "world"})
```

## Returning a JSON Response

You can also serve JSON responses when serving HTTP request using the following way.

```python
from robyn import jsonify


@app.post("/jsonify")
async def json(request):
    return jsonify({"hello": "world"})
```

## Format of the Response

Robyn supports several kinds of Response for your routes

#### Dictionary

Robyn accepts dictionaries to build a response for the route:

```python
@app.post("/dictionary")
async def dictionary(request):
    return {
        "status_code": 200,
        "description": "This is a regular response",
        "type": "text",
        "headers": {"Header": "header_value"},
    }
```

#### Response object

Robyn provides a `Response` object to help you build a valid response.

```python
from robyn.robyn import Response


@app.get("/response")
async def response(request):
    return Response(status_code=200, headers={}, description="OK")
```

#### Status Codes

Robyn provides `StatusCodes` if you want to return type safe Status Responses.

```python

from robyn import status_codes


@app.get("/response")
async def response(request):
    return Response(status_code=status_codes.HTTP_200_OK, headers={}, description="OK")
```

#### Returning a byte response
You can also return byte response when serving HTTP requests using the following way

```python
@app.get("/binary_output_response_sync")
def binary_output_response_sync(request):
    return Response(
        status_code=200,
        headers={"Content-Type": "application/octet-stream"},
        description="OK",
    )


@app.get("/binary_output_async")
async def binary_output_async(request):
    return b"OK"


@app.get("/binary_output_response_async")
async def binary_output_response_async(request):
    return Response(
        status_code=200,
        headers={"Content-Type": "application/octet-stream"},
        description="OK",
    )
```


#### Other types

Whenever you want to use another type for your routes, the `str` method will be called on it, and it will be stored in the body of the response. Here is an example that returns a string:

```python
@app.get("/")
async def hello(request):
    return "Hello World"
```

## Global Request Headers

You can also add global headers for every request.

```python
app.add_request_header("server", "robyn")
```

## Global Response Headers

You can also add global response headers for every request.

```python
app.add_response_header("content-type", "application/json")
```

## Per route headers

You can also add request and response headers for every route.

```python
@app.before_request("/sync/middlewares")
def sync_before_request(request: Request):
    request.headers["before"] = "sync_before_request"
    return request
```

```python
@app.after_request("/sync/middlewares")
def sync_after_request(response: Response):
    response.headers["after"] = "sync_after_request"
    response.description = response.description + " after"
    return response
```


Additionally, you can access headers for per route.

```python
@app.get("/test-headers")
def sync_middle_of_request(request: Request):
    request.headers["test"] = "we are modifying the request headers in the middle of the request!"
    print(request)
```

## Query Params

You can access query params from every HTTP method.

For the url: `http://localhost:8080/query?a=b`

You can use the following code snippet.

```python
@app.get("/query")
async def query_get(request):
    query_data = request.queries
    return jsonify(query_data)
```

## Events

You can add startup and shutdown events in Robyn. These events will execute before the requests have started serving and after the serving has been completed.

```python
async def startup_handler():
    print("Starting up")


app.startup_handler(startup_handler)


@app.shutdown_handler
def shutdown_handler():
    print("Shutting down")
```

## WebSockets

You can now serve WebSockets using Robyn.

Firstly, you need to create a WebSocket Class and wrap it around your Robyn app.

```python
from robyn import Robyn, jsonify, WebSocket


app = Robyn(__file__)
websocket = WebSocket(app, "/web_socket")
```

Now, you can define 3 methods for every WebSocket for their life cycle, they are as follows:

```python
@websocket.on("message")
def message():
    global i
    i += 1
    if i == 0:
        return "Whaaat??"
    elif i == 1:
        return "Whooo??"
    elif i == 2:
        return "*chika* *chika* Slim Shady."
    elif i == 3:
        i = -1
        return ""


@websocket.on("close")
def close():
    return "Goodbye world, from ws"


@websocket.on("connect")
def connect():
    return "Hello world, from ws"
```

The three methods:

- "message" is called when the socket receives a message
- "close" is called when the socket is disconnected
- "connect" is called when the socket connects

To see a complete service in action, you can go to the folder [../integration_tests/base_routes.py](../integration_tests/base_routes.py)

#### WebSocket Usage

You can also use async functions for WebSockets.

```python
@websocket.on("message")
async def message():
    global i
    i += 1
    if i == 0:
        return "Whaaat??"
    elif i == 1:
        return "Whooo??"
    elif i == 2:
        return "*chika* *chika* Slim Shady."
    elif i == 3:
        i = -1
        return ""


@websocket.on("close")
async def close():
    return "Goodbye world, from ws"


@websocket.on("connect")
async def connect():
    return "Hello world, from ws"
```

## Middlewares

You can use both sync and async functions for middlewares!

```python
@app.before_request("/")
async def hello_before_request(request: Request):
    request.headers["before"] = "async_before_request"
    print(request)


@app.after_request("/")
def hello_after_request(response: Response):
    response.headers["after"] = "sync_after_request"
    print(response)
```

Middlewares can be bound to a route or run before/after every request:

```python
# This middleware runs before all requests
@app.before_request()
async def global_before_request(request: Request):
    request.headers["before"] = "global_before_request"

# This middleware runs only before requests to "/your/route"
@app.before_request("/your/route")
async def route_before_request(request: Request):
    request.headers["before"] = "route_before_request"
```

In the before middleware, you can choose to directly return a `Response` object. When doing so, the route method and the after middlewares will not be executed.

```python
def is_user_logged(request: Request):
    # Check the validity of a JWT cookie for example
    ...

@app.before_request("/")
async def hello_before_request(request: Request):
    if not is_user_logged(request):
        # The request is aborted, we are returning an error before reaching the route method
        return Response(401, {}, "User isn't logged in!")

@app.get("/")
async def route(request: Request):
    print("This won't be executed if user isn't logged in")

@app.after_request("/")
async def hello_after_request(response: Response):
    print("This won't be executed if user isn't logged in")
```

## Authentication

Robyn provides an easy way to add an authentication middleware to your application. You can then specify `auth_required=True` in your routes to make them accessible only to authenticated users.

```python
@app.get("/auth", auth_required=True)
async def auth(request: Request):
    # This route method will only be executed if the user is authenticated
    # Otherwise, a 401 response will be returned
    return "Hello, world"
```

To add an authentication middleware, you can use the `configure_authentication` method. This method requires an `AuthenticationHandler` object as an argument. This object specifies how to authenticate a user, and uses a `TokenGetter` object to retrieve the token from the request. Robyn does currently provide a `BearerGetter` class that gets the token from the `Authorization` header, using the `Bearer` scheme. Here is an example of a basic authentication handler:

```python
class BasicAuthHandler(AuthenticationHandler):
    def authenticate(self, request: Request) -> Optional[Identity]:
        token = self.token_getter.get_token(request)
        if token == "valid":
            return Identity(claims={})
        return None

app.configure_authentication(BasicAuthHandler(token_getter=BearerGetter()))
```

Your `authenticate` method should return an `Identity` object if the user is authenticated, or `None` otherwise. The `Identity` object can contain any data you want, and will be accessible in your route methods using the `request.identity` attribute.

Note that this authentication system is basically only using a "before request" middleware under the hood. This means you can overlook it and create your own authentication system using middlewares if you want to. However, Robyn still provide this easy to implement solution that should suit most use cases.

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

## Templates

You can render templates in Robyn. We ship `Jinja2` as our out-of-the-box solution. If you would like to add support for other templating engines you can create your own renderer too! Read more at [templating](/templates.md) documentation.

Here is a sample below.

main.py

```python
from robyn.templating import JinjaTemplate

current_file_path = pathlib.Path(__file__).parent.resolve()
JINJA_TEMPLATE = JinjaTemplate(os.path.join(current_file_path, "templates"))


@app.get("/template_render")
def template_render():
    context = {"framework": "Robyn", "templating_engine": "Jinja2"}

    template = JINJA_TEMPLATE.render_template(template_name="test.html", **context)
    return template
```

templates/test.html

```html
{# templates/test.html #}

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Results</title>
</head>

<body>
  <h1>{{framework}} 🤝 {{templating_engine}}</h1>
</body>
</html>
```

### Understanding the code

Inside your project, you need to have a directory to store the templates, called `templates` in our case.

You can store and any `Jinja2` templates inside that directory. We are calling it `test.html`.

## Views

To organise your code in a better way - either to group by responsibility or for code splitting, you can use `views`.

A view, simply is a function with a collection of other closures. e.g.
```python
def sample_view():
    def get():
        return "Hello, world!"

    def post(request):
        body = request.body
        return {"status_code": 200, "description": body}
```

The above view contains two closures for the `get` and the `post` request.

You can serve views in two ways:

1. Using an `@app.view` decorator.
```python
@app.view("/sync/view/decorator")
def sync_decorator_view():
    def get():
        return "Hello, world!"

    def post(request):
        body = request.body
        return {"status_code": 200, "description": body}


@app.view("/async/view/decorator")
def async_decorator_view():
    async def get():
        return "Hello, world!"

    async def post(request):
        body = request.body
        return {"status_code": 200, "description": body}
```


2. Importing it from a different file.

```python
#views.py
def View():
    async def get():
        return "Hello, world!"

    async def post(request):
        body = request.body
        return {
            "status": 200,
            "description": body,
            "headers": {"Content-Type": "text/json"},
        }
```

And then in `app.py`:

```python
from .views import View

...
...

app.add_view("/", View)

```

## Route Registration

Instead of using the decorators, you can also add routes with a function:

```python
async def hello(request):
    return "Hello World"

app.add_route("GET", "/hello", hello)
```

This works for all HTTP methods.

## Allow CORS

You can allow CORS for your application by adding the following code:

```python
from robyn import Robyn, ALLOW_CORS

app = Robyn(__file__)
ALLOW_CORS(app)
```

## Exceptions

You can raise exceptions in your code and Robyn will handle them for you.

```python
@app.exception
def handle_exception(error):
    return {"status_code": 500, "description": f"error msg: {error}"}

```

## SubRouters

You can create subrouters in Robyn. This is useful when you want to group routes together.

Subrouters can be used for both normal routes and WebSockets. They are basically a mini version of the main router and can be used in the same way.

The only caveat is that you need to add the subrouter to the main router.

```python
from robyn import Robyn, SubRouter

app = Robyn(__file__)

sub_router = SubRouter(__file__, "/sub_router")

@sub_router.get("/hello")
def hello():
    return "Hello, world"

app.include_router(sub_router)
```
