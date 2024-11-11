import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_subroute_authentication(session, function_type: str):
    r = get(f"/sub_router/{function_type}/auth", headers={"Authorization": "Bearer valid"})
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_subroute_authentication_token(session, function_type: str):
    r = get(
        f"/sub_router/{function_type}/auth",
        headers={"Authorization": "Bearer invalid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_subroute_authentication_header(session, function_type: str):
    r = get(
        f"/sub_router/{function_type}/auth",
        headers={"Authorization": "Bear valid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_subroute_authentication_no_token(session, function_type: str):
    r = get(f"/sub_router/{function_type}/auth", should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"
