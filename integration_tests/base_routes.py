import os


import pathlib

from robyn import WS, Robyn, Request, Response, jsonify, serve_file, serve_html
from robyn.templating import JinjaTemplate


from views import SyncView, AsyncView

app = Robyn(__file__)
websocket = WS(app, "/web_socket")

current_file_path = pathlib.Path(__file__).parent.resolve()
jinja_template = JinjaTemplate(os.path.join(current_file_path, "templates"))

# ===== Websockets =====

websocket_state = 0


@websocket.on("message")
async def connect(websocket_id):
    global websocket_state
    if websocket_state == 0:
        response = "Whaaat??"
    elif websocket_state == 1:
        response = "Whooo??"
    elif websocket_state == 2:
        response = "*chika* *chika* Slim Shady."
    websocket_state = (websocket_state + 1) % 3
    return response


@websocket.on("close")
def close():
    return "GoodBye world, from ws"


@websocket.on("connect")
def message():
    return "Hello world, from ws"


# ===== Lifecycle handlers =====


async def startup_handler():
    print("Starting up")


@app.shutdown_handler
def shutdown_handler():
    print("Shutting down")


# ===== Middlewares =====


@app.before_request("/sync/middlewares")
def sync_before_request(request: Request):
    request.headers["before"] = "sync_before_request"
    return request


@app.after_request("/sync/middlewares")
def sync_after_request(response: Response):
    response.headers["after"] = "sync_after_request"
    response.body = response.body + " after"
    return response


@app.get("/sync/middlewares")
def sync_middlewares(request: Request):
    assert "before" in request.headers
    assert request.headers["before"] == "sync_before_request"
    return "sync middlewares"


@app.before_request("/async/middlewares")
async def async_before_request(request: Request):
    request.headers["before"] = "async_before_request"
    return request


@app.after_request("/async/middlewares")
async def async_after_request(response: Response):
    response.headers["after"] = "async_after_request"
    response.body = response.body + " after"
    return response


@app.get("/async/middlewares")
async def async_middlewares(request: Request):
    assert "before" in request.headers
    assert request.headers["before"] == "async_before_request"
    return "async middlewares"


# ===== Routes =====

# --- GET ---

# Hello world


@app.get("/")
async def hello_world():
    return "Hello world"


# str


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
    return {
        "status_code": 200,
        "body": "sync dict get",
        "type": "text",
        "headers": {"sync": "dict"},
    }


@app.get("/async/dict")
async def async_dict_get():
    return {
        "status_code": 200,
        "body": "async dict get",
        "type": "text",
        "headers": {"async": "dict"},
    }


@app.get("/sync/dict/const", const=True)
def sync_dict_const_get():
    return {
        "status_code": 200,
        "body": "sync dict const get",
        "type": "text",
        "headers": {"sync_const": "dict"},
    }


@app.get("/async/dict/const", const=True)
async def async_dict_const_get():
    return {
        "status_code": 200,
        "body": "async dict const get",
        "type": "text",
        "headers": {"async_const": "dict"},
    }


# Response


@app.get("/sync/response")
def sync_response_get():
    return Response(200, {"sync": "response"}, "sync response get")


@app.get("/async/response")
async def async_response_get():
    return Response(200, {"async": "response"}, "async response get")


@app.get("/sync/response/const", const=True)
def sync_response_const_get():
    return Response(200, {"sync_const": "response"}, "sync response const get")


@app.get("/async/response/const", const=True)
async def async_response_const_get():
    return Response(200, {"async_const": "response"}, "async response const get")


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
        headers={"Content-Type": "application/octet-stream"},
        body="sync octet response",
    )


@app.get("/async/octet/response")
async def async_octet_response_get():
    return Response(
        status_code=200,
        headers={"Content-Type": "application/octet-stream"},
        body="async octet response",
    )


# JSON


@app.get("/sync/json")
def sync_json_get():
    return jsonify({"sync json get": "json"})


@app.get("/async/json")
async def async_json_get():
    return jsonify({"async json get": "json"})


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


# Queries


@app.get("/sync/queries")
def sync_queries(request: Request):
    query_data = request.queries
    return jsonify(query_data)


@app.get("/async/queries")
async def async_query(request: Request):
    query_data = request.queries
    return jsonify(query_data)


# Status code


@app.get("/404")
def return_404():
    return {"status_code": 404, "body": "not found", "type": "text"}


@app.get("/202")
def return_202():
    return {"status_code": 202, "body": "hello", "type": "text"}


@app.get("/307")
async def redirect():
    return {
        "status_code": 307,
        "body": "",
        "type": "text",
        "headers": {"Location": "redirect_route"},
    }


@app.get("/redirect_route")
async def redirect_route():
    return "This is the redirected route"


@app.get("/sync/raise")
def sync_raise():
    raise Exception()


@app.get("/async/raise")
async def async_raise():
    raise Exception()


# --- POST ---

# dict


@app.post("/sync/dict")
def sync_dict_post():
    return {
        "status_code": 200,
        "body": "sync dict post",
        "type": "text",
        "headers": {"sync": "dict"},
    }


@app.post("/async/dict")
async def async_dict_post():
    return {
        "status_code": 200,
        "body": "async dict post",
        "type": "text",
        "headers": {"async": "dict"},
    }


# Body


@app.post("/sync/body")
def sync_body_post(request: Request):
    return request.body


@app.post("/async/body")
async def async_body_post(request: Request):
    return request.body


# --- PUT ---

# dict


@app.put("/sync/dict")
def sync_dict_put():
    return {
        "status_code": 200,
        "body": "sync dict put",
        "type": "text",
        "headers": {"sync": "dict"},
    }


@app.put("/async/dict")
async def async_dict_put():
    return {
        "status_code": 200,
        "body": "async dict put",
        "type": "text",
        "headers": {"async": "dict"},
    }


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
    return {
        "status_code": 200,
        "body": "sync dict delete",
        "type": "text",
        "headers": {"sync": "dict"},
    }


@app.delete("/async/dict")
async def async_dict_delete():
    return {
        "status_code": 200,
        "body": "async dict delete",
        "type": "text",
        "headers": {"async": "dict"},
    }


# Body


@app.delete("/sync/body")
def sync_body_delete(request: Request):
    return request.body


@app.delete("/async/body")
async def async_body_delete(request: Request):
    return request.body


# --- PATCH ---

# dict


@app.patch("/sync/dict")
def sync_dict_patch():
    return {
        "status_code": 200,
        "body": "sync dict patch",
        "type": "text",
        "headers": {"sync": "dict"},
    }


@app.patch("/async/dict")
async def async_dict_patch():
    return {
        "status_code": 200,
        "body": "async dict patch",
        "type": "text",
        "headers": {"async": "dict"},
    }


# Body


@app.patch("/sync/body")
def sync_body_patch(request: Request):
    return request.body


@app.patch("/async/body")
async def async_body_patch(request: Request):
    return request.body


# ===== Views =====


@app.view("/sync/view/decorator")
def sync_decorator_view():
    def get():
        return "Hello, world!"

    def post(request: Request):
        body = request.body
        return {"status_code": 200, "body": body}


@app.view("/async/view/decorator")
def async_decorator_view():
    async def get():
        return "Hello, world!"

    async def post(request: Request):
        body = request.body
        return {"status_code": 200, "body": body}


# ===== Main =====


if __name__ == "__main__":
    app.add_response_header("server", "robyn")
    app.add_directory(
        route="/test_dir",
        directory_path=os.path.join(current_file_path, "build"),
        index_file="index.html",
    )
    app.startup_handler(startup_handler)
    app.add_view("/sync/view", SyncView)
    app.add_view("/async/view", AsyncView)
    app.start(port=8080)
