import asyncio
import logging
import os
import pathlib

from robyn import WS, Robyn, jsonify, serve_file, serve_html
from robyn.log_colors import Colors
from robyn.robyn import Response
from robyn.templating import JinjaTemplate

app = Robyn(__file__)
websocket = WS(app, "/web_socket")
i = -1

logger = logging.getLogger(__name__)
current_file_path = pathlib.Path(__file__).parent.resolve()
jinja_template = JinjaTemplate(os.path.join(current_file_path, "templates"))


@websocket.on("message")
async def connect(websocket_id):
    print(websocket_id)
    global i
    i += 1
    if i == 0:
        return "Whaaat??"
    elif i == 1:
        return "Whooo??"
    elif i == 2:
        i = -1
        return "*chika* *chika* Slim Shady."


@websocket.on("close")
def close():
    return "GoodBye world, from ws"


@websocket.on("connect")
def message():
    return "Hello world, from ws"


callCount = 0


@app.get("/")
async def hello(request):
    global callCount
    callCount += 1
    message = "Called " + str(callCount) + " times"
    print(message, request)
    return {"status_code": 200, "body": "hello", "type": "text"}


@app.get("/const_request", const=True)
async def const_request():
    return "Hello world"


@app.get("/const_request_json", const=True)
async def const_request_json():
    return jsonify({"hello": "world"})


@app.get("/const_request_headers", const=True)
async def const_request_headers():
    return {
        "status_code": 200,
        "body": "",
        "type": "text",
        "headers": {"Header": "header_value"},
    }


@app.get("/request_headers")
async def request_headers():
    return {
        "status_code": 200,
        "body": "This is a regular response",
        "type": "text",
        "headers": {"Header": "header_value"},
    }


@app.get("/404")
def return_404():
    return {"status_code": 404, "body": "hello", "type": "text"}


@app.post("/404")
def return_404_post():
    return {"status_code": 404, "body": "hello", "type": "text"}


@app.get("/int_status_code")
def return_int_status_code():
    return {"status_code": 202, "body": "hello", "type": "text"}


@app.before_request("/")
async def hello_before_request(request):
    global callCount
    callCount += 1
    print(request)
    return ""


@app.after_request("/")
async def hello_after_request(request):
    global callCount
    callCount += 1
    print(request)
    return ""


@app.get("/test/:id")
async def test(request):
    print(request)
    current_file_path = pathlib.Path(__file__).parent.resolve()
    html_file = os.path.join(current_file_path, "index.html")

    return serve_html(html_file)


@app.get("/template_render")
async def template_render():
    context = {"framework": "Robyn", "templating_engine": "Jinja2"}

    template = jinja_template.render_template(template_name="test.html", **context)
    return template


@app.get("/jsonify")
async def json_get():
    return jsonify({"hello": "world"})


@app.get("/query")
async def query_get(request):
    query_data = request["queries"]
    return jsonify(query_data)


@app.post("/jsonify/:id")
async def json(request):
    return jsonify({"hello": "world"})


@app.post("/post")
async def post():
    return "POST Request"


@app.post("/post_with_body")
async def postreq_with_body(request):
    return bytearray(request["body"]).decode("utf-8")


@app.put("/put")
async def put(request):
    return "PUT Request"


@app.put("/put_with_body")
async def putreq_with_body(request):
    print(request)
    return bytearray(request["body"]).decode("utf-8")


@app.post("/headers")
async def postreq_with_headers(request):
    logger.info(f"{Colors.OKGREEN} {request['headers']} \n{Colors.ENDC}")
    return jsonify(request["headers"])


@app.delete("/delete")
async def delete():
    return "DELETE Request"


@app.delete("/delete_with_body")
async def deletereq_with_body(request):
    return bytearray(request["body"]).decode("utf-8")


@app.patch("/patch")
async def patch():
    return "PATCH Request"


@app.patch("/patch_with_body")
async def patchreq_with_body(request):
    return bytearray(request["body"]).decode("utf-8")


@app.get("/sleep")
async def sleeper():
    await asyncio.sleep(5)
    return "sleep function"


@app.get("/blocker")
def blocker():
    import time

    time.sleep(10)
    return "blocker function"


async def startup_handler():
    print("Starting up")


@app.shutdown_handler
def shutdown_handler():
    print("Shutting down")


@app.get("/redirect")
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


@app.get("/types/response")
def response_type(request):
    return Response(status_code=200, headers={}, body="OK")


@app.get("/types/str")
def str_type(request):
    return "OK"


@app.get("/types/int")
def int_type(request):
    return 0


@app.get("/async/types/response")
async def async_response_type(request):
    return Response(status_code=200, headers={}, body="OK")


@app.get("/async/types/str")
async def async_str_type(request):
    return "OK"


@app.get("/async/types/int")
async def async_int_type(request):
    return 0


@app.get("/file_download_sync")
def file_download_sync():
    current_file_path = pathlib.Path(__file__).parent.resolve()
    file_path = os.path.join(current_file_path, "downloads", "test.txt")
    return serve_file(file_path)


@app.get("/file_download_async")
def file_download_async():
    current_file_path = pathlib.Path(__file__).parent.resolve()
    file_path = os.path.join(current_file_path, "downloads", "test.txt")
    return serve_file(file_path)


@app.get("/sync/raise")
def sync_raise():
    raise Exception()


@app.get("/async/raise")
async def async_raise():
    raise Exception()


if __name__ == "__main__":
    app.add_request_header("server", "robyn")
    current_file_path = pathlib.Path(__file__).parent.resolve()
    app.add_directory(
        route="/test_dir",
        directory_path=os.path.join(current_file_path, "build"),
        index_file="index.html",
    )
    app.startup_handler(startup_handler)
    app.start(port=8080)
