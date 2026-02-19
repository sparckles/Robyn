import asyncio
import json
import os
import pathlib
import time
from collections import defaultdict
from typing import Optional

from integration_tests.subroutes import di_subrouter, static_router, sub_router
from robyn import Headers, Request, Response, Robyn, SSEMessage, SSEResponse, WebSocketDisconnect, jsonify, serve_file, serve_html
from robyn.authentication import AuthenticationHandler, BearerGetter, Identity
from robyn.robyn import QueryParams, Url
from robyn.templating import JinjaTemplate
from robyn.types import Body, JsonBody, JSONResponse, Method, PathParams

app = Robyn(__file__)

current_file_path = pathlib.Path(__file__).parent.resolve()
jinja_template = JinjaTemplate(os.path.join(current_file_path, "templates"))

# ===== Websockets =====

# Make it easier for multiple test runs
websocket_state = defaultdict(int)


# --- Regular WebSocket endpoint (new-style with Rust channels) ---
@app.websocket("/web_socket")
async def websocket_endpoint(websocket):
    try:
        while True:
            _ = await websocket.receive_text()
            websocket_id = websocket.id
            global websocket_state
            state = websocket_state[websocket_id]

            if state == 0:
                await websocket.broadcast("This is a broadcast message")
                await websocket.send_text("This is a message to self")
                await websocket.send_text("Whaaat??")
            elif state == 1:
                await websocket.send_text("Whooo??")
            elif state == 2:
                await websocket.broadcast(websocket.query_params.get("one", ""))
                await websocket.send_text(websocket.query_params.get("two", ""))
                await websocket.send_text("*chika* *chika* Slim Shady.")
            elif state == 3:
                await websocket.send_text("Connection closed")
                await websocket.close()
                break

            websocket_state[websocket_id] = (state + 1) % 4
    except WebSocketDisconnect:
        pass


@websocket_endpoint.on_connect
def websocket_on_connect(websocket):
    return "Hello world, from ws"


@websocket_endpoint.on_close
def websocket_on_close(websocket):
    return "GoodBye world, from ws"


# --- JSON WebSocket endpoint ---
@app.websocket("/web_socket_json")
async def json_websocket_endpoint(websocket):
    try:
        while True:
            msg = await websocket.receive_text()
            websocket_id = websocket.id
            response = {"ws_id": websocket_id, "resp": "", "msg": msg}
            global websocket_state
            state = websocket_state[websocket_id]

            if state == 0:
                response["resp"] = "Whaaat??"
            elif state == 1:
                response["resp"] = "Whooo??"
            elif state == 2:
                response["resp"] = "*chika* *chika* Slim Shady."

            websocket_state[websocket_id] = (state + 1) % 3
            await websocket.send_json(response)
    except WebSocketDisconnect:
        pass


@json_websocket_endpoint.on_connect
def json_websocket_on_connect(websocket):
    return "Hello world, from ws"


@json_websocket_endpoint.on_close
def json_websocket_on_close(websocket):
    return "GoodBye world, from ws"


# --- WebSocket with dependency injection ---
@app.websocket("/web_socket_di")
async def di_websocket_endpoint(websocket, global_dependencies=None, router_dependencies=None):
    try:
        while True:
            _ = await websocket.receive_text()
            global_dep = global_dependencies.get("GLOBAL_DEPENDENCY", "MISSING GLOBAL") if global_dependencies else "MISSING GLOBAL"
            router_dep = router_dependencies.get("ROUTER_DEPENDENCY", "MISSING ROUTER") if router_dependencies else "MISSING ROUTER"
            await websocket.send_text(f"handler: {global_dep} {router_dep}")
    except WebSocketDisconnect:
        pass


@di_websocket_endpoint.on_connect
async def di_websocket_on_connect(websocket, global_dependencies=None, router_dependencies=None):
    global_dep = global_dependencies.get("GLOBAL_DEPENDENCY") if global_dependencies else "MISSING GLOBAL"
    router_dep = router_dependencies.get("ROUTER_DEPENDENCY") if router_dependencies else "MISSING ROUTER"
    return f"connect: {global_dep} {router_dep}"


@di_websocket_endpoint.on_close
async def di_websocket_on_close(websocket, global_dependencies=None):
    global_dep = global_dependencies.get("GLOBAL_DEPENDENCY") if global_dependencies else "MISSING GLOBAL"
    return f"close: {global_dep}"


# --- WebSocket with empty returns ---
@app.websocket("/web_socket_empty_returns")
async def empty_websocket_endpoint(websocket):
    try:
        while True:
            await websocket.receive_text()
            # No response sent
    except WebSocketDisconnect:
        pass


@empty_websocket_endpoint.on_connect
async def empty_websocket_on_connect(websocket):
    """Test async handler with no return"""
    pass


@empty_websocket_endpoint.on_close
async def empty_websocket_on_close(websocket):
    """Test async handler with explicit None return"""
    return None


# ===== Lifecycle handlers =====


async def startup_handler():
    print("Starting up")


@app.shutdown_handler
def shutdown_handler():
    print("Shutting down")


# ===== Middlewares =====

# --- Global ---


@app.before_request()
def global_before_request(request: Request):
    request.headers.set("global_before", "global_before_request")
    return request


@app.after_request()
def global_after_request(response: Response):
    response.headers.set("global_after", "global_after_request")
    return response


@app.get("/sync/global/middlewares")
def sync_global_middlewares(request: Request):
    print(request.headers)
    print(request.headers.get("txt"))
    print(request.headers["txt"])
    assert "global_before" in request.headers
    assert request.headers.get("global_before") == "global_before_request"
    return "sync global middlewares"


# --- Route specific ---


@app.before_request("/sync/middlewares")
def sync_before_request(request: Request):
    request.headers.set("before", "sync_before_request")
    return request


@app.after_request("/sync/middlewares")
def sync_after_request(response: Response):
    response.headers.set("after", "sync_after_request")
    response.description = response.description + " after"
    return response


@app.get("/sync/middlewares")
def sync_middlewares(request: Request):
    assert "before" in request.headers
    assert request.headers.get("before") == "sync_before_request"
    assert request.ip_addr == "127.0.0.1"
    return "sync middlewares"


@app.before_request("/async/middlewares")
async def async_before_request(request: Request):
    request.headers.set("before", "async_before_request")
    return request


@app.after_request("/async/middlewares")
async def async_after_request(response: Response):
    response.headers.set("after", "async_after_request")
    response.description = response.description + " after"
    return response


@app.get("/async/middlewares")
async def async_middlewares(request: Request):
    assert "before" in request.headers
    assert request.headers.get("before") == "async_before_request"
    assert request.ip_addr == "127.0.0.1"
    return "async middlewares"


@app.before_request("/sync/middlewares/401")
def sync_before_request_401():
    return Response(401, Headers({}), "sync before request 401")


@app.get("/sync/middlewares/401")
def sync_middlewares_401():
    pass


# ===== Routes =====

# --- GET ---

# Hello world

app.inject(RouterDependency="Router Dependency")


@app.get("/", openapi_name="Index")
async def hello_world(r):
    """
    Get hello world
    """
    return "Hello, world!"


@app.get("/trailing")
def trailing_slash(request):
    return "Trailing slash test successful!"


@app.get("/sync/str")
def sync_str_get():
    return "sync str get"


@app.get("/async/str")
async def async_str_get():
    return "async str get"


@app.get("/sync/str/const", const=True)
def sync_str_const_get():
    return "sync str const get"


@app.get("/async/str/const", const=True)
async def async_str_const_get():
    return "async str const get"


# dict


@app.get("/sync/dict")
def sync_dict_get():
    return Response(
        status_code=200,
        description="sync dict get",
        headers={"sync": "dict"},
    )


@app.get("/async/dict")
async def async_dict_get():
    return Response(
        status_code=200,
        description="async dict get",
        headers={"async": "dict"},
    )


@app.get("/sync/dict/const", const=True)
def sync_dict_const_get():
    return Response(
        status_code=200,
        description="sync dict const get",
        headers={"sync_const": "dict"},
    )


@app.get("/async/dict/const", const=True)
async def async_dict_const_get():
    return Response(
        status_code=200,
        description="async dict const get",
        headers={"async_const": "dict"},
    )


# Response


@app.get("/sync/response")
def sync_response_get():
    return Response(200, Headers({"sync": "response"}), "sync response get")


@app.get("/async/response")
async def async_response_get():
    return Response(200, Headers({"async": "response"}), "async response get")


@app.get("/sync/response/const", const=True)
def sync_response_const_get():
    return Response(200, Headers({"sync_const": "response"}), "sync response const get")


@app.get("/async/response/const", const=True)
async def async_response_const_get():
    return Response(200, Headers({"async_const": "response"}), "async response const get")


# Binary


@app.get("/sync/octet")
def sync_octet_get():
    return b"sync octet"


@app.get("/async/octet")
async def async_octet_get():
    return b"async octet"


@app.get("/sync/octet/response")
def sync_octet_response_get():
    return Response(
        status_code=200,
        headers=Headers({"Content-Type": "application/octet-stream"}),
        description="sync octet response",
    )


@app.get("/async/octet/response")
async def async_octet_response_get():
    return Response(
        status_code=200,
        headers=Headers({"Content-Type": "application/octet-stream"}),
        description="async octet response",
    )


# JSON


@app.get("/sync/json")
def sync_json_get():
    return jsonify({"sync json get": "json"})


@app.get("/async/json")
async def async_json_get():
    return jsonify({"async json get": "json"})


# JSON List (auto-serialized without explicit jsonify)


@app.get("/sync/json/list")
def sync_json_list_get():
    return [
        {"id": 1, "title": "First Post", "published": True},
        {"id": 2, "title": "Draft Post", "published": False},
        {"id": 3, "title": "Latest Post", "published": True},
    ]


@app.get("/async/json/list")
async def async_json_list_get():
    return [
        {"id": 1, "title": "First Post", "published": True},
        {"id": 2, "title": "Draft Post", "published": False},
        {"id": 3, "title": "Latest Post", "published": True},
    ]


@app.get("/sync/json/list/empty")
def sync_json_list_empty_get():
    return []


@app.get("/async/json/list/empty")
async def async_json_list_empty_get():
    return []


@app.get("/sync/json/list/primitives")
def sync_json_list_primitives_get():
    return [1, 2, 3, "four", True, None]


@app.get("/async/json/list/primitives")
async def async_json_list_primitives_get():
    return [1, 2, 3, "four", True, None]


# JSON Dict (auto-serialized without explicit jsonify)


@app.get("/sync/json/dict")
def sync_json_dict_get():
    return {"message": "sync dict", "count": 42, "active": True}


@app.get("/async/json/dict")
async def async_json_dict_get():
    return {"message": "async dict", "count": 42, "active": True}


@app.get("/sync/json/const", const=True)
def sync_json_const_get():
    return jsonify({"sync json const get": "json"})


@app.get("/async/json/const", const=True)
async def async_json_const_get():
    return jsonify({"async json const get": "json"})


# Param


@app.get("/sync/param/:id")
def sync_param(request: Request):
    id = request.path_params["id"]
    return id


@app.get("/async/param/:id")
async def async_param(request: Request):
    id = request.path_params["id"]
    return id


@app.get("/sync/extra/*extra")
def sync_param_extra(request: Request):
    extra = request.path_params["extra"]
    return extra


@app.get("/async/extra/*extra")
async def async_param_extra(request: Request):
    extra = request.path_params["extra"]
    return extra


# Request Info


@app.get("/sync/http/param")
def sync_http_param(request: Request):
    return jsonify(
        {
            "url": {
                "scheme": request.url.scheme,
                "host": request.url.host,
                "path": request.url.path,
            },
            "method": request.method,
        }
    )


@app.get("/async/http/param")
async def async_http_param(request: Request):
    return jsonify(
        {
            "url": {
                "scheme": request.url.scheme,
                "host": request.url.host,
                "path": request.url.path,
            },
            "method": request.method,
        }
    )


# HTML serving


@app.get("/sync/serve/html")
def sync_serve_html():
    html_file = os.path.join(current_file_path, "index.html")
    return serve_html(html_file)


@app.get("/async/serve/html")
async def async_serve_html():
    html_file = os.path.join(current_file_path, "index.html")
    return serve_html(html_file)


# Template


@app.get("/sync/template")
def sync_template_render():
    context = {"framework": "Robyn", "templating_engine": "Jinja2"}
    template = jinja_template.render_template(template_name="test.html", **context)
    return template


@app.get("/async/template")
async def async_template_render():
    context = {"framework": "Robyn", "templating_engine": "Jinja2"}
    template = jinja_template.render_template(template_name="test.html", **context)
    return template


# File download


@app.get("/sync/file/download")
def sync_file_download():
    file_path = os.path.join(current_file_path, "downloads", "test.txt")
    return serve_file(file_path)


@app.get("/async/file/download")
async def file_download_async():
    file_path = os.path.join(current_file_path, "downloads", "test.txt")
    return serve_file(file_path)


# Multipart file


@app.post("/sync/multipart-file")
def sync_multipart_file(request: Request):
    files = request.files
    file_names = files.keys()
    return {"file_names": list(file_names)}


# Queries


@app.get("/sync/queries")
def sync_queries(request: Request):
    query_data = request.query_params.to_dict()
    return jsonify(query_data)


@app.get("/async/queries")
async def async_query(request: Request):
    query_data = request.query_params.to_dict()
    return jsonify(query_data)


# Status code


@app.get("/404")
def return_404():
    return Response(status_code=404, description="not found", headers={"Content-Type": "text"})


@app.get("/202")
def return_202():
    return Response(status_code=202, description="hello", headers={"Content-Type": "text"})


@app.get("/307")
async def redirect():
    return Response(
        status_code=307,
        description="",
        headers={"Location": "redirect_route"},
    )


@app.get("/redirect_route")
async def redirect_route():
    return "This is the redirected route"


@app.get("/sync/raise")
def sync_raise():
    raise Exception()


@app.get("/async/raise")
async def async_raise():
    raise Exception()


# cookie
@app.get("/cookie")
def cookie():
    response = Response(status_code=200, headers=Headers({}), description="test cookies")
    response.set_cookie(key="fakesession", value="fake-cookie-session-value")

    return response


@app.get("/cookie/multiple")
def multiple_cookies():
    response = Response(status_code=200, headers=Headers({}), description="test multiple cookies")
    response.set_cookie(key="session", value="abc123")
    response.set_cookie(key="theme", value="dark")
    return response


@app.get("/cookie/attributes")
def cookie_with_attributes():
    response = Response(status_code=200, headers=Headers({}), description="test cookie attributes")
    response.set_cookie(
        key="secure_session",
        value="secret123",
        path="/",
        http_only=True,
        secure=True,
        same_site="Strict",
        max_age=3600,
    )
    return response


@app.get("/cookie/overwrite")
def cookie_overwrite():
    response = Response(status_code=200, headers=Headers({}), description="test cookie overwrite")
    response.set_cookie(key="session", value="first-value")
    response.set_cookie(key="session", value="final-value")  # Should overwrite
    return response


# --- POST ---

# dict


@app.post("/sync/dict")
def sync_dict_post():
    return Response(
        status_code=200,
        description="sync dict post",
        headers={"sync": "dict"},
    )


@app.post("/async/dict")
async def async_dict_post():
    return Response(
        status_code=200,
        description="async dict post",
        headers={"async": "dict"},
    )


# Body


@app.post("/sync/body")
def sync_body_post(request: Request):
    return request.body


@app.post("/async/body")
async def async_body_post(request: Request):
    return request.body


@app.post("/sync/form_data")
def sync_form_data(request: Request):
    return request.headers["Content-Type"]


# JSON Request


@app.post("/sync/request_json")
def sync_json_post(request: Request):
    try:
        return type(request.json())
    except ValueError:
        return None


@app.post("/async/request_json")
async def async_json_post(request: Request):
    try:
        return type(request.json())
    except ValueError:
        return None


@app.post("/sync/request_json/key")
async def request_json(request: Request):
    json = request.json()
    return json["key"]


# JSON type preservation test
@app.post("/sync/request_json/types")
def sync_json_types(request: Request):
    """Returns the JSON data with Python type names for verification"""
    data = request.json()
    result = {}
    for key, value in data.items():
        result[key] = {
            "value": value,
            "type": type(value).__name__,
        }
    return result


@app.post("/async/request_json/types")
async def async_json_types(request: Request):
    """Returns the JSON data with Python type names for verification"""
    data = request.json()
    result = {}
    for key, value in data.items():
        result[key] = {
            "value": value,
            "type": type(value).__name__,
        }
    return result


# JSON top-level array test (Issue #1145)
@app.post("/sync/request_json/array")
def sync_json_array(request: Request):
    """Returns the parsed JSON when the body is a top-level array"""
    data = request.json()
    return {"parsed": data, "type": type(data).__name__}


@app.post("/async/request_json/array")
async def async_json_array(request: Request):
    """Returns the parsed JSON when the body is a top-level array"""
    data = request.json()
    return {"parsed": data, "type": type(data).__name__}


# --- PUT ---

# dict


@app.put("/sync/dict")
def sync_dict_put():
    return Response(
        status_code=200,
        description="sync dict put",
        headers={"sync": "dict"},
    )


@app.put("/async/dict")
async def async_dict_put():
    return Response(
        status_code=200,
        description="async dict put",
        headers={"async": "dict"},
    )


# Body


@app.put("/sync/body")
def sync_body_put(request: Request):
    return request.body


@app.put("/async/body")
async def async_body_put(request: Request):
    return request.body


# --- DELETE ---

# dict


@app.delete("/sync/dict")
def sync_dict_delete():
    return Response(
        status_code=200,
        description="sync dict delete",
        headers={"sync": "dict"},
    )


@app.delete("/async/dict")
async def async_dict_delete():
    return Response(
        status_code=200,
        description="async dict delete",
        headers={"async": "dict"},
    )


# Body


@app.delete("/sync/body")
def sync_body_delete(request: Request):
    print(request.body)
    return request.body


@app.delete("/async/body")
async def async_body_delete(request: Request):
    return request.body


# --- PATCH ---

# dict


@app.patch("/sync/dict")
def sync_dict_patch():
    return Response(
        status_code=200,
        description="sync dict patch",
        headers={"sync": "dict"},
    )


@app.patch("/async/dict")
async def async_dict_patch():
    return Response(
        status_code=200,
        description="async dict patch",
        # need to fix this
        headers={"async": "dict"},
    )


# Body


@app.patch("/sync/body")
def sync_body_patch(request: Request):
    return request.body


@app.patch("/async/body")
async def async_body_patch(request: Request):
    return request.body


# ==== Exception Handling ====


@app.exception
def handle_exception(error):
    return Response(status_code=500, description=f"error msg: {error}", headers={})


@app.get("/sync/exception/get")
def sync_exception_get():
    raise ValueError("value error")


@app.get("/async/exception/get")
async def async_exception_get():
    raise ValueError("value error")


@app.put("/sync/exception/put")
def sync_exception_put(request: Request):
    raise ValueError("value error")


@app.put("/async/exception/put")
async def async_exception_put(request: Request):
    raise ValueError("value error")


@app.post("/sync/exception/post")
def sync_exception_post(request: Request):
    raise ValueError("value error")


@app.post("/async/exception/post")
async def async_exception_post(request: Request):
    raise ValueError("value error")


# ===== Authentication =====


@app.get("/sync/auth", auth_required=True)
def sync_auth(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@app.get("/async/auth", auth_required=True)
async def async_auth(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


# ===== Main =====


def sync_without_decorator():
    return "Success!"


async def async_without_decorator():
    return "Success!"


app.add_route("GET", "/sync/get/no_dec", sync_without_decorator)
app.add_route("PUT", "/sync/put/no_dec", sync_without_decorator)
app.add_route("POST", "/sync/post/no_dec", sync_without_decorator)
app.add_route("GET", "/async/get/no_dec", async_without_decorator)
app.add_route("PUT", "/async/put/no_dec", async_without_decorator)
app.add_route("POST", "/async/post/no_dec", async_without_decorator)

# ===== Dependency Injection =====

GLOBAL_DEPENDENCY = "GLOBAL DEPENDENCY"
ROUTER_DEPENDENCY = "ROUTER DEPENDENCY"

app.inject_global(GLOBAL_DEPENDENCY=GLOBAL_DEPENDENCY)
app.inject(ROUTER_DEPENDENCY=ROUTER_DEPENDENCY)


@app.get("/sync/global_di")
def sync_global_di(request, router_dependencies, global_dependencies):
    return global_dependencies["GLOBAL_DEPENDENCY"]


@app.get("/sync/router_di")
def sync_router_di(request, router_dependencies):
    return router_dependencies["ROUTER_DEPENDENCY"]


# ===== Split request body =====


@app.get("/sync/split_request_untyped/query_params")
def sync_split_request_untyped_basic(query_params):
    return query_params.to_dict()


@app.get("/async/split_request_untyped/query_params")
async def async_split_request_untyped_basic(query_params):
    return query_params.to_dict()


@app.get("/sync/split_request_untyped/headers")
def sync_split_request_untyped_headers(headers):
    return headers.get("server")


@app.get("/async/split_request_untyped/headers")
async def async_split_request_untyped_headers(headers):
    return headers.get("server")


@app.get("/sync/split_request_untyped/path_params/:id")
def sync_split_request_untyped_path_params(path_params):
    return path_params


@app.get("/async/split_request_untyped/path_params/:id")
async def async_split_request_untyped_path_params(path_params):
    return path_params


@app.get("/sync/split_request_untyped/method")
def sync_split_request_untyped_method(method):
    return method


@app.get("/async/split_request_untyped/method")
async def async_split_request_untyped_method(method):
    return method


@app.post("/sync/split_request_untyped/body")
def sync_split_request_untyped_body(body):
    return body


@app.post("/async/split_request_untyped/body")
async def async_split_request_untyped_body(body):
    return body


@app.post("/sync/split_request_untyped/combined")
def sync_split_request_untyped_combined(body, query_params, method, url, headers):
    return {
        "body": body,
        "query_params": query_params.to_dict(),
        "method": method,
        "url": url.path,
        "headers": headers.get("server"),
    }


@app.post("/async/split_request_untyped/combined")
async def async_split_request_untyped_combined(body, query_params, method, url, headers):
    return {
        "body": body,
        "query_params": query_params.to_dict(),
        "method": method,
        "url": url.path,
        "headers": headers.get("server"),
    }


@app.get("/sync/split_request_typed/query_params")
def sync_split_request_basic(query_data: QueryParams):
    return query_data.to_dict()


@app.get("/async/split_request_typed/query_params")
async def async_split_request_basic(query_data: QueryParams):
    return query_data.to_dict()


@app.get("/sync/split_request_typed/headers")
def sync_split_request_headers(request_headers: Headers):
    return request_headers.get("server")


@app.get("/async/split_request_typed/headers")
async def async_split_request_headers(request_headers: Headers):
    return request_headers.get("server")


@app.get("/sync/split_request_typed/path_params/:id")
def sync_split_request_path_params(path_data: PathParams):
    return path_data


@app.get("/async/split_request_typed/path_params/:id")
async def async_split_request_path_params(path_data: PathParams):
    return path_data


@app.get("/sync/split_request_typed/method")
def sync_split_request_method(request_method: Method):
    return request_method


@app.get("/async/split_request_typed/method")
async def async_split_request_method(request_method: Method):
    return request_method


@app.post("/sync/split_request_typed/body")
def sync_split_request_body(request_body: Body):
    return request_body


@app.post("/async/split_request_typed/body")
async def async_split_request_body(request_body: Body):
    return request_body


@app.post("/sync/split_request_typed/combined")
def sync_split_request_combined(
    request_body: Body,
    query_data: QueryParams,
    request_method: Method,
    request_url: Url,
    request_headers: Headers,
):
    return {
        "body": request_body,
        "query_params": query_data.to_dict(),
        "method": request_method,
        "url": request_url.path,
        "headers": request_headers.get("server"),
    }


@app.post("/async/split_request_typed/combined")
async def async_split_request_combined(
    request_body: Body,
    query_data: QueryParams,
    request_method: Method,
    request_url: Url,
    request_headers: Headers,
):
    return {
        "body": request_body,
        "query_params": query_data.to_dict(),
        "method": request_method,
        "url": request_url.path,
        "headers": request_headers.get("server"),
    }


@app.post("/sync/split_request_typed_untyped/combined")
def sync_split_request_typed_untyped_combined(
    query_params,
    request_method: Method,
    request_body: Body,
    url: Url,
    headers: Headers,
):
    return {
        "body": request_body,
        "query_params": query_params.to_dict(),
        "method": request_method,
        "url": url.path,
        "headers": headers.get("server"),
    }


@app.post("/async/split_request_typed_untyped/combined")
async def async_split_request_typed_untyped_combined(
    query_params,
    request_method: Method,
    request_body: Body,
    url: Url,
    headers: Headers,
):
    return {
        "body": request_body,
        "query_params": query_params.to_dict(),
        "method": request_method,
        "url": url.path,
        "headers": headers.get("server"),
    }


@app.post("/sync/split_request_typed_untyped/combined/failure")
def sync_split_request_typed_untyped_combined_failure(query_params, request_method: Method, request_body: Body, url: Url, headers: Headers, vishnu):
    return {
        "body": request_body,
        "query_params": query_params.to_dict(),
        "method": request_method,
        "url": url.path,
        "headers": headers.get("server"),
        "vishnu": vishnu,
    }


@app.post("/async/split_request_typed_untyped/combined/failure")
async def async_split_request_typed_untyped_combined_failure(query_params, request_method: Method, request_body: Body, url: Url, headers: Headers, vishnu):
    return {
        "body": request_body,
        "query_params": query_params.to_dict(),
        "method": request_method,
        "url": url.path,
        "headers": headers.get("server"),
        "vishnu": vishnu,
    }


@app.get("/openapi_test", openapi_tags=["test tag"])
def sample_openapi_endpoint():
    """Get openapi"""
    return 200


class Initial(Body):
    is_present: bool
    letter: Optional[str]


class FullName(Body):
    first: str
    second: str
    initial: Initial


class CreateItemBody(Body):
    name: FullName
    description: str
    price: float
    tax: float


class CreateItemResponse(JSONResponse):
    success: bool
    items_changed: int


class CreateItemQueryParamsParams(QueryParams):
    required: bool


@app.post("/openapi_request_body")
def create_item(request, body: CreateItemBody, query: CreateItemQueryParamsParams) -> CreateItemResponse:
    return CreateItemResponse(success=True, items_changed=2)


# ===== JsonBody Routes =====


class TemperatureInput(JsonBody):
    fahrenheit: float


@app.post("/sync/json_body/bare")
def sync_json_body_bare(data: JsonBody):
    """Bare JsonBody - receives parsed JSON dict"""
    return data


@app.post("/async/json_body/bare")
async def async_json_body_bare(data: JsonBody):
    """Bare JsonBody - receives parsed JSON dict"""
    return data


@app.post("/sync/json_body/typed")
def sync_json_body_typed(data: TemperatureInput):
    """Typed JsonBody - receives parsed JSON dict, docs show schema"""
    fahrenheit = data.get("fahrenheit", 0)
    celsius = (float(fahrenheit) - 32) * 5 / 9
    return {"celsius": celsius}


@app.post("/async/json_body/typed")
async def async_json_body_typed(data: TemperatureInput):
    """Typed JsonBody - receives parsed JSON dict, docs show schema"""
    fahrenheit = data.get("fahrenheit", 0)
    celsius = (float(fahrenheit) - 32) * 5 / 9
    return {"celsius": celsius}


@app.post("/openapi_json_body")
def openapi_json_body_endpoint(request: Request, data: TemperatureInput) -> dict:
    """Convert fahrenheit to celsius using JsonBody"""
    return {"celsius": (float(data.get("fahrenheit", 0)) - 32) * 5 / 9}


# ===== Server-Sent Events (SSE) Routes =====


@app.get("/sse/basic")
def sse_basic(request):
    """Basic SSE endpoint that sends 3 messages"""

    def event_generator():
        for i in range(3):
            yield f"data: Test message {i}\n\n"

    return SSEResponse(event_generator())


@app.get("/sse/formatted")
def sse_formatted(request):
    """SSE endpoint using SSEMessage formatter"""

    def event_generator():
        for i in range(3):
            yield SSEMessage(f"Formatted message {i}", event="test", id=str(i))

    return SSEResponse(event_generator())


@app.get("/sse/json")
def sse_json(request):
    """SSE endpoint that sends JSON data"""

    def event_generator():
        for i in range(3):
            data = {"id": i, "message": f"JSON message {i}", "type": "test"}
            yield f"data: {json.dumps(data)}\n\n"

    return SSEResponse(event_generator())


@app.get("/sse/named_events")
def sse_named_events(request):
    """SSE endpoint with different event types"""

    def event_generator():
        events = [("start", "Test started"), ("progress", "Test in progress"), ("end", "Test completed")]
        for event_type, message in events:
            yield SSEMessage(message, event=event_type)

    return SSEResponse(event_generator())


@app.get("/sse/async")
async def sse_async(request):
    """Async SSE endpoint with true async generator support"""

    async def async_event_generator():
        """True async generator for SSE events"""
        for i in range(3):
            await asyncio.sleep(0.1)  # Simulate async work
            yield SSEMessage(f"Async message {i}", event="async", id=str(i))

    return SSEResponse(async_event_generator())


@app.get("/sse/streaming_sync")
def sse_streaming_sync(request):
    """SSE endpoint to test real-time sync streaming"""

    def streaming_generator():
        for i in range(3):
            yield SSEMessage(f"Streaming sync message {i} at {time.strftime('%H:%M:%S')}", id=str(i))
            time.sleep(0.5)  # 500ms delay to test streaming
        yield SSEMessage("Streaming test completed", event="end")

    return SSEResponse(streaming_generator())


@app.get("/sse/streaming_async")
async def sse_streaming_async(request):
    """SSE endpoint to test real-time async streaming"""

    async def streaming_async_generator():
        for i in range(3):
            await asyncio.sleep(0.3)  # 300ms delay
            yield SSEMessage(f"Streaming async message {i} at {time.strftime('%H:%M:%S')}", event="async", id=str(i))
        yield SSEMessage("Async streaming test completed", event="end")

    return SSEResponse(streaming_async_generator())


@app.get("/sse/high_frequency")
def sse_high_frequency(request):
    """SSE endpoint to test high frequency streaming"""

    def high_freq_generator():
        for i in range(20):
            yield SSEMessage(f"Fast message {i}", id=str(i))
            time.sleep(0.05)  # 50ms = 20 messages per second
        yield SSEMessage("High frequency test completed", event="end")

    return SSEResponse(high_freq_generator())


@app.get("/sse/single")
def sse_single(request):
    """SSE endpoint that sends a single message and closes"""

    def event_generator():
        yield "data: Single message\n\n"

    return SSEResponse(event_generator())


@app.get("/sse/empty")
def sse_empty(request):
    """SSE endpoint that sends no messages"""

    def event_generator():
        return
        yield  # This will never be reached

    return SSEResponse(event_generator())


@app.get("/sse/with_headers")
def sse_with_headers(request):
    """SSE endpoint with custom headers"""
    headers = Headers({"X-Custom-Header": "custom-value"})

    def event_generator():
        yield "data: Message with custom headers\n\n"

    return SSEResponse(event_generator(), headers=headers)


@app.get("/sse/status_code")
def sse_status_code(request):
    """SSE endpoint with custom status code"""

    def event_generator():
        yield "data: Message with custom status\n\n"

    return SSEResponse(event_generator(), status_code=201)


def main():
    app.set_response_header("server", "robyn")
    app.serve_directory(
        route="/test_dir",
        directory_path=os.path.join(current_file_path, "build"),
        index_file="index.html",
    )
    # Serving static files at /static from ./integration_tests.
    app.serve_directory(
        route="/static",
        directory_path=str(current_file_path),
    )
    app.startup_handler(startup_handler)
    app.include_router(sub_router)
    app.include_router(di_subrouter)
    app.include_router(static_router)

    class BasicAuthHandler(AuthenticationHandler):
        def authenticate(self, request: Request) -> Optional[Identity]:
            token = self.token_getter.get_token(request)
            if token is not None:
                # Useless but we call the set_token method for testing purposes
                self.token_getter.set_token(request, token)
            if token == "valid":
                return Identity(claims={"key": "value"})
            return None

    app.configure_authentication(BasicAuthHandler(token_getter=BearerGetter()))

    # Read port from environment variable if set, otherwise default to 8080
    port = int(os.getenv("ROBYN_PORT", "8080"))
    app.start(port=port, _check_port=False)


if __name__ == "__main__":
    main()
