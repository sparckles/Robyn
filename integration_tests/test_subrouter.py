import pytest
from websocket import create_connection

from integration_tests.helpers.http_methods_helpers import generic_http_helper, head


@pytest.mark.parametrize(
    "http_method_type",
    ["get", "post", "put", "delete", "patch", "options", "trace"],
)
@pytest.mark.benchmark
def test_sub_router(http_method_type, session):
    response = generic_http_helper(http_method_type, "sub_router/foo")
    assert response.json() == {"message": "foo"}


@pytest.mark.benchmark
def test_sub_router_head(session):
    response = head("sub_router/foo")
    assert response.text == ""  # response body is expected to be empty


@pytest.mark.benchmark
def test_sub_router_web_socket(session):
    BASE_URL = "ws://127.0.0.1:8080"
    ws = create_connection(f"{BASE_URL}/sub_router/ws")
    assert ws.recv() == "Hello world, from ws"
    ws.send("My name is?")
    assert ws.recv() == "Message"


@pytest.mark.benchmark
def test_nested_sub_router_get(session):
    # nested SubRouter prefixes must accumulate: /sub_router + /nested + /foo (#865, #1394)
    response = generic_http_helper("get", "sub_router/nested/foo")
    assert response.json() == {"message": "nested foo"}


@pytest.mark.benchmark
def test_nested_sub_router_add_route(session):
    # route registered via add_route on the nested SubRouter must also be prefixed (#1256)
    response = generic_http_helper("get", "sub_router/nested/added")
    assert response.json() == {"message": "nested added"}


@pytest.mark.benchmark
def test_nested_sub_router_web_socket(session):
    BASE_URL = "ws://127.0.0.1:8080"
    ws = create_connection(f"{BASE_URL}/sub_router/nested/ws")
    assert ws.recv() == "Hello world, from nested ws"
    ws.send("ping")
    assert ws.recv() == "nested message"
