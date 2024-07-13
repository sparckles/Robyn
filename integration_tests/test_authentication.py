import pytest
from base64 import b64encode
from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication(session, function_type: str):
    r = get(f"/{function_type}/auth", headers={"Authorization": "Bearer valid"})
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_token(session, function_type: str):
    r = get(
        f"/{function_type}/auth",
        headers={"Authorization": "Bearer invalid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_header(session, function_type: str):
    r = get(
        f"/{function_type}/auth",
        headers={"Authorization": "Bear valid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_no_token(session, function_type: str):
    r = get(f"/{function_type}/auth", should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
def test_nested_router_valid_authentication(session):
    r = get("/di_subrouter/main-nest/nested-1/nested-2/nested-route-2", headers={"Authorization": "Bearer valid"})
    assert r.text == "This is a route inside nested_router_2."


@pytest.mark.benchmark
def test_nested_router_invalid_authentication_token(session):
    r = get(
        "/di_subrouter/main-nest/nested-1/nested-2/nested-route-2",
        headers={"Authorization": "Bearer invalid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
def test_nested_router_invalid_authentication_header(session):
    r = get(
        "/di_subrouter/main-nest/nested-1/nested-2/nested-route-2",
        headers={"Authorization": "Bear valid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
def test_nested_router_invalid_authentication_no_token(session):
    r = get("/di_subrouter/main-nest/nested-1/nested-2/nested-route-2", should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication_bearer_2(session, function_type: str):
    r = get(f"/{function_type}/auth/bearer-2", headers={"Authorization": "Bearer valid-2"})
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_token_bearer_2(session, function_type: str):
    r = get(
        f"/{function_type}/auth/bearer-2",
        headers={"Authorization": "Bearer invalid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_header_bearer_2(session, function_type: str):
    r = get(
        f"/{function_type}/auth/bearer-2",
        headers={"Authorization": "Bear valid-2"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_no_token_bearer_2(session, function_type: str):
    r = get(f"/{function_type}/auth/bearer-2", should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication_basic(session, function_type: str):
    r = get(f"/{function_type}/auth/basic", headers={"Authorization": f"Basic {b64encode('valid:valid'.encode()).decode()}"})
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_token_basic(session, function_type: str):
    r = get(
        f"/{function_type}/auth/basic",
        headers={"Authorization": "Basic invalid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BasicGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_header_basic(session, function_type: str):
    r = get(
        f"/{function_type}/auth/basic",
        headers={"Authorization": "Bear valid-2"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BasicGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_no_token_basic(session, function_type: str):
    r = get(f"/{function_type}/auth/basic", should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BasicGetter"
