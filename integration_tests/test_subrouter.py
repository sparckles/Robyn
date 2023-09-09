from websocket import create_connection
import pytest

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
