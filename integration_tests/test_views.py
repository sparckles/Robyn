from integration_tests.helpers.http_methods_helpers import get, post
import pytest


@pytest.mark.benchmark
def test_get_sync_view(session):
    r = get("/sync/view")
    assert r.text == "Hello, world!"


@pytest.mark.benchmark
def test_post_sync_view(session):
    r = post("/sync/view", data={"name": "John"})
    assert "John" in r.text


@pytest.mark.benchmark
def test_get_sync_decorator_view(session):
    r = get("/sync/view/decorator")
    assert r.text == "Hello, world!"


@pytest.mark.benchmark
def test_post_sync_decorator_view(session):
    r = post("/sync/view/decorator", data={"name": "John"})
    assert "John" in r.text


@pytest.mark.benchmark
def test_get_async_view(session):
    r = get("/async/view")
    assert r.text == "Hello, world!"


@pytest.mark.benchmark
def test_post_async_view(session):
    r = post("/async/view", data={"name": "John"})
    assert "John" in r.text


@pytest.mark.benchmark
def test_get_async_decorator_view(session):
    r = get("/async/view/decorator")
    assert r.text == "Hello, world!"


@pytest.mark.benchmark
def test_post_async_decorator_view(session):
    r = post("/async/view/decorator", data={"name": "John"})
    assert "John" in r.text
