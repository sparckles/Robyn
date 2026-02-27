from robyn import SubRouter, WebSocketDisconnect, jsonify

from .di_subrouter import di_subrouter
from .file_api import static_router

sub_router = SubRouter(prefix="/sub_router")

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
