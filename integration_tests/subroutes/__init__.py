from robyn import SubRouter, WebSocketDisconnect, jsonify

from .di_subrouter import di_subrouter
from .file_api import static_router

sub_router = SubRouter(__name__, prefix="/sub_router")

__all__ = ["sub_router", "di_subrouter", "static_router"]


@sub_router.websocket("/ws")
async def ws_handler(websocket):
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_text("Message")
    except WebSocketDisconnect:
        pass


@ws_handler.on_connect
async def connect(websocket):
    return "Hello world, from ws"


@ws_handler.on_close
async def close(websocket):
    return jsonify({"message": "closed"})


@sub_router.get("/foo")
def get_foo():
    return {"message": "foo"}


@sub_router.post("/foo")
def post_foo():
    return {"message": "foo"}


@sub_router.put("/foo")
def put_foo():
    return {"message": "foo"}


@sub_router.delete("/foo")
def delete_foo():
    return {"message": "foo"}


@sub_router.patch("/foo")
def patch_foo():
    return {"message": "foo"}


@sub_router.options("/foo")
def option_foo():
    return {"message": "foo"}


@sub_router.trace("/foo")
def trace_foo():
    return {"message": "foo"}


@sub_router.head("/foo")
def head_foo():
    return {"message": "foo"}


@sub_router.post("/openapi_test", openapi_tags=["test subrouter tag"])
def sample_subrouter_openapi_endpoint():
    """Get subrouter openapi"""
    return 200


# Nested SubRouter to verify prefix accumulation for HTTP routes, add_route, and
# WebSockets (#865, #1394, #1256). It is included into sub_router (prefix
# "/sub_router"), so these endpoints become reachable at /sub_router/nested/*.
nested_sub_router = SubRouter(__name__, prefix="/nested")


@nested_sub_router.get("/foo")
def nested_get_foo():
    return {"message": "nested foo"}


def nested_added_route():
    return {"message": "nested added"}


# add_route on a SubRouter must apply the prefix too (#1256)
nested_sub_router.add_route("GET", "/added", nested_added_route)


@nested_sub_router.websocket("/ws")
async def nested_ws_handler(websocket):
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_text("nested message")
    except WebSocketDisconnect:
        pass


@nested_ws_handler.on_connect
async def nested_connect(websocket):
    return "Hello world, from nested ws"


@nested_ws_handler.on_close
async def nested_close(websocket):
    return jsonify({"message": "nested closed"})


sub_router.include_router(nested_sub_router)
