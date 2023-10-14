from robyn import SubRouter, jsonify, WebSocket


sub_router = SubRouter(__name__, prefix="/sub_router")

websocket = WebSocket(sub_router, "/ws")


@websocket.on("connect")
async def connect(ws):
    return "Hello world, from ws"


@websocket.on("message")
async def message():
    return "Message"


@websocket.on("close")
async def close(ws):
    return jsonify({"message": "closed"})


@sub_router.get("/foo")
def get_foo(name):
    return jsonify({"message": "foo"})


@sub_router.post("/foo")
def post_foo(name):
    return jsonify({"message": "foo"})


@sub_router.put("/foo")
def put_foo(name):
    return jsonify({"message": "foo"})


@sub_router.delete("/foo")
def delete_foo(name):
    return jsonify({"message": "foo"})


@sub_router.patch("/foo")
def patch_foo(name):
    return jsonify({"message": "foo"})


@sub_router.options("/foo")
def option_foo(name):
    return jsonify({"message": "foo"})


@sub_router.trace("/foo")
def trace_foo(name):
    return jsonify({"message": "foo"})


@sub_router.head("/foo")
def head_foo(name):
    return jsonify({"message": "foo"})
