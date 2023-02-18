from http_methods_helpers import get, post


def test_view(session):
    r = get("/test_view")
    assert r.status_code == 200
    assert r.text == "Get Request!"

    r = post("/test_view", data={"name": "John"})
    assert r.status_code == 200
    assert r.text == "Post Request!"


def test_decorator_view(session):
    r = get("/test_decorator_view")
    assert r.status_code == 200
    assert r.text == "Hello, world!"

    r = post("/test_decorator_view")
    assert r.status_code == 200
    assert r.text == "Hello, world!"
