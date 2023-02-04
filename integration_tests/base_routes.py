import os
import pathlib

from robyn import WS, Robyn, jsonify, serve_file, serve_html
from robyn.robyn import Response
from robyn.templating import JinjaTemplate

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


@app.before_request("/")
async def hello_before_request(request):
    request["headers"]["before"] = "before_request"
    return request


@app.after_request("/")
async def hello_after_request(request):
    request["headers"]["after"] = "after_request"
    return request


@app.get("/")
async def middlewares():
    return ""


# ===== Routes =====

# --- GET ---

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
def sync_param(request):
    id = request["params"]["id"]
    return id


@app.get("/async/param/:id")
async def async_param(request):
    id = request["params"]["id"]
    return id


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
def sync_queries(request):
    query_data = request["queries"]
    return jsonify(query_data)


@app.get("/async/queries")
async def async_query(request):
    query_data = request["queries"]
    return jsonify(query_data)


# Status code


@app.get("/404")
def return_404():
    return {"status_code": 404, "body": "not found", "type": "text"}


@app.get("/202")
def return_202():
    return {"status_code": 202, "body": "hello", "type": "text"}


@app.get("/307")
async def redirect(request):
    return {
        "status_code": 307,
        "body": "",
        "type": "text",
        "headers": {"Location": "redirect_route"},
    }


@app.get("/redirect_route")
async def redirect_route(request):
    return "This is the redirected route"


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
def sync_body_post(request):
    return bytearray(request["body"]).decode("utf-8")


@app.post("/async/body")
async def async_body_post(request):
    return bytearray(request["body"]).decode("utf-8")


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
def sync_body_put(request):
    return bytearray(request["body"]).decode("utf-8")


@app.put("/async/body")
async def async_body_put(request):
    return bytearray(request["body"]).decode("utf-8")


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
def sync_body_delete(request):
    return bytearray(request["body"]).decode("utf-8")


@app.delete("/async/body")
async def async_body_delete(request):
    return bytearray(request["body"]).decode("utf-8")


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
def sync_body_patch(request):
    return bytearray(request["body"]).decode("utf-8")


@app.patch("/async/body")
async def async_body_patch(request):
    return bytearray(request["body"]).decode("utf-8")


@app.get("/binary_output_sync")
def binary_output_sync(request):
    return b"OK"


@app.get("/binary_output_response_sync")
def binary_output_response_sync(request):
    return Response(
        status_code=200,
        headers={"Content-Type": "application/octet-stream"},
        body="OK",
    )


@app.get("/binary_output_async")
async def binary_output_async(request):
    return b"OK"


@app.get("/binary_output_response_async")
async def binary_output_response_async(request):
    return Response(
        status_code=200,
        headers={"Content-Type": "application/octet-stream"},
        body="OK",
    )


@app.get("/sync/raise")
def sync_raise():
    raise Exception()


@app.get("/async/raise")
async def async_raise():
    raise Exception()


# ===== Main =====


if __name__ == "__main__":
    app.add_request_header("server", "robyn")
    app.add_directory(
        route="/test_dir",
        directory_path=os.path.join(current_file_path, "build"),
        index_file="index.html",
    )
    app.startup_handler(startup_handler)
    app.start(port=8080)
