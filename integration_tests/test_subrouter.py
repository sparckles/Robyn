from robyn import Robyn, SubRouter, jsonify

app = Robyn(__name__)

router = SubRouter(__name__, prefix="/subrouter")


@router.get("/foo")
def get_foo(name):
    return jsonify({"message": "foo"})


@router.put("/foo")
def put_foo(name):
    return jsonify({"message": "foo"})


@router.delete("/foo")
def delete_foo(name):
    return jsonify({"message": "foo"})


@router.patch("/foo")
def patch_foo(name):
    return jsonify({"message": "foo"})


@router.options("/foo")
def option_foo(name):
    return jsonify({"message": "foo"})


@router.trace("/foo")
def trace_foo(name):
    return jsonify({"message": "foo"})


@router.head("/foo")
def head_foo(name):
    return jsonify({"message": "foo"})


app.include_router(router)

app.start()
