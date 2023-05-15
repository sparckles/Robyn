from robyn import SubRouter, jsonify


sub_router = SubRouter(__name__, prefix="/sub_router")


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
