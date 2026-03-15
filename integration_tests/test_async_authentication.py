import pytest

from integration_tests.helpers.http_methods_helpers import get


# --- Async authentication handler (SubRouter with its own async handler) ---


@pytest.mark.benchmark
def test_async_auth_handler_valid_token(session):
    r = get("/async_auth_sub/protected", headers={"Authorization": "Bearer valid"})
    assert r.text == "async_auth_protected"


@pytest.mark.benchmark
def test_async_auth_handler_invalid_token(session):
    r = get(
        "/async_auth_sub/protected",
        headers={"Authorization": "Bearer invalid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
def test_async_auth_handler_no_token(session):
    r = get("/async_auth_sub/protected", should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


# --- Inherited authentication (SubRouter without its own handler, inherits parent's) ---


@pytest.mark.benchmark
def test_inherited_auth_valid_token(session):
    r = get("/inherited_auth_sub/protected", headers={"Authorization": "Bearer valid"})
    assert r.text == "inherited_auth_protected"


@pytest.mark.benchmark
def test_inherited_auth_invalid_token(session):
    r = get(
        "/inherited_auth_sub/protected",
        headers={"Authorization": "Bearer invalid"},
        should_check_response=False,
    )
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
def test_inherited_auth_no_token(session):
    r = get("/inherited_auth_sub/protected", should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"
