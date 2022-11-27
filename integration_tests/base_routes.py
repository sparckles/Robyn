from robyn import Robyn, static_file, jsonify, WS

from robyn.templating import JinjaTemplate

from robyn.log_colors import Colors
import asyncio
import os
import pathlib
import logging

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
    return {"status_code": "200", "body": "hello", "type": "text"}


@app.get("/const_request", const=True)
async def const_request():
    return "Hello world"


@app.get("/const_request_json", const=True)
async def const_request_json():
    return jsonify({"hello": "world"})


@app.get("/404")
def return_404():
    return {"status_code": "404", "body": "hello", "type": "text"}


@app.post("/404")
def return_404_post():
    return {"status_code": "404", "body": "hello", "type": "text"}


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

    return static_file(html_file)


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
        "status_code": "307",
        "body": "",
        "type": "text",
        "headers": jsonify({"Location": "redirect_route"}),
    }


@app.get("/redirect_route")
async def redirect_route(request):
    return "This is the redirected route"


if __name__ == "__main__":
    app.add_header("server", "robyn")
    current_file_path = pathlib.Path(__file__).parent.resolve()
    app.add_directory(
        route="/test_dir",
        directory_path=os.path.join(current_file_path, "build"),
        index_file="index.html",
    )
    app.startup_handler(startup_handler)
    app.start(port=5000)
