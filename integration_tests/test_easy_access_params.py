import pytest
from websocket import create_connection

from integration_tests.helpers.http_methods_helpers import get

WS_BASE_URL = "ws://127.0.0.1:8080"


# ===== HTTP: Path param + query param with type coercion =====


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_path_and_query_params(session, function_type):
    r = get(f"/easy/{function_type}/42?q=hello&page=5")
    assert r.json() == {"id": 42, "q": "hello", "page": 5}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_default_value(session, function_type):
    r = get(f"/easy/{function_type}/42?q=hello")
    assert r.json() == {"id": 42, "q": "hello", "page": 1}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_missing_required_param(session, function_type):
    """Missing required 'q' param should return 400."""
    r = get(f"/easy/{function_type}/42", should_check_response=False)
    assert r.status_code == 400


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_bad_type_coercion(session, function_type):
    """Path param :id declared as int but given 'abc' should return 400."""
    r = get(f"/easy/{function_type}/abc?q=hello", should_check_response=False)
    assert r.status_code == 400


# ===== HTTP: Optional params =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_optional_present(session, function_type):
    r = get(f"/easy/{function_type}/optional?name=bob&age=30")
    assert r.json() == {"name": "bob", "age": 30}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_optional_missing(session, function_type):
    r = get(f"/easy/{function_type}/optional?name=bob")
    assert r.json() == {"name": "bob", "age": None}


# ===== HTTP: List params =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_list_params(session, function_type):
    r = get(f"/easy/{function_type}/list?tag=python&tag=rust&tag=web")
    assert r.json() == {"tags": ["python", "rust", "web"]}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_list_single_value(session, function_type):
    r = get(f"/easy/{function_type}/list?tag=python")
    assert r.json() == {"tags": ["python"]}


# ===== HTTP: Bool params =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_bool_true(session, function_type):
    r = get(f"/easy/{function_type}/bool?active=true")
    assert r.json() == {"active": True}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_bool_false(session, function_type):
    r = get(f"/easy/{function_type}/bool?active=false")
    assert r.json() == {"active": False}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_bool_default(session, function_type):
    r = get(f"/easy/{function_type}/bool")
    assert r.json() == {"active": False}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_bool_numeric(session, function_type):
    r = get(f"/easy/{function_type}/bool?active=1")
    assert r.json() == {"active": True}


# ===== HTTP: Mixed (Request object + individual params) =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_mixed_with_request(session, function_type):
    r = get(f"/easy/{function_type}/mixed/99?q=search")
    assert r.json() == {"id": 99, "q": "search", "method": "GET"}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_mixed_with_default(session, function_type):
    r = get(f"/easy/{function_type}/mixed/99")
    assert r.json() == {"id": 99, "q": "", "method": "GET"}


# ===== HTTP: Float params =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_float(session, function_type):
    r = get(f"/easy/{function_type}/float?price=19.99")
    assert r.json() == {"price": 19.99}


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_easy_access_float_bad_value(session, function_type):
    r = get(f"/easy/{function_type}/float?price=notanumber", should_check_response=False)
    assert r.status_code == 400


# ===== WebSocket: Easy access query params =====


def test_easy_access_ws_with_params(session):
    ws = create_connection(f"{WS_BASE_URL}/web_socket_easy_access?room=chat&page=5")
    connect_msg = ws.recv()
    assert connect_msg == "connected to chat"

    ws.send("hello")
    response = ws.recv()
    assert response == "room=chat page=5 msg=hello"

    ws.close()


def test_easy_access_ws_with_defaults(session):
    ws = create_connection(f"{WS_BASE_URL}/web_socket_easy_access")
    connect_msg = ws.recv()
    assert connect_msg == "connected to default"

    ws.send("hello")
    response = ws.recv()
    assert response == "room=default page=1 msg=hello"

    ws.close()
