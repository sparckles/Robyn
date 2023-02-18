from helpers.http_methods_helpers import get, post


def test_get_async_view(session):
    r = get("/sync_view")
    assert r.status_code == 200
    assert r.text == "Hello, world!"


def test_post_async_view(session):
    r = post("/sync_view", data={"name": "John"})
    assert r.status_code == 200
    assert "John" in r.text


def test_get_async_decorator_view(session):
    r = get("/sync_decorator_view")
    assert r.status_code == 200
    assert r.text == "Hello, world!"


def test_post_async_decorator_view(session):
    r = post("/sync_decorator_view", data={"name": "John"})
    assert r.status_code == 200
    assert "John" in r.text
