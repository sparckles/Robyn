import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication_endpoint(session, function_type: str):
    r = get(f"/auth_subrouter_endpoint/auth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_endpoint(session, function_type: str):
    r = get(f"/auth_subrouter_endpoint/auth_subroute_{function_type}", headers={"Authorization": "Bearer invalid"}, should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication_include(session, function_type: str):
    r = get(f"/auth_subrouter_include/auth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_include(session, function_type: str):
    r = get(f"/auth_subrouter_include/auth_subroute_{function_type}", headers={"Authorization": "Bearer invalid"}, should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_no_authentication_include(session, function_type: str):
    r = get(f"/auth_subrouter_include/noauth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "bypassed"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication_instance(session, function_type: str):
    r = get(f"/auth_subrouter_instance/auth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_instance(session, function_type: str):
    r = get(f"/auth_subrouter_instance/auth_subroute_{function_type}", headers={"Authorization": "Bearer invalid"}, should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_no_authentication_instance(session, function_type: str):
    r = get(f"/auth_subrouter_instance/noauth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "bypassed"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication_include_false(session, function_type: str):
    r = get(f"/auth_subrouter_include_false/auth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_include_false(session, function_type: str):
    r = get(f"/auth_subrouter_include_false/auth_subroute_{function_type}", headers={"Authorization": "Bearer invalid"}, should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_no_authentication_include_false(session, function_type: str):
    r = get(f"/auth_subrouter_include_false/noauth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "bypassed"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication_include_true(session, function_type: str):
    r = get(f"/auth_subrouter_include_true/auth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_include_true(session, function_type: str):
    r = get(f"/auth_subrouter_include_true/auth_subroute_{function_type}", headers={"Authorization": "Bearer invalid"}, should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_no_authentication_include_true(session, function_type: str):
    r = get(f"/auth_subrouter_include_true/noauth_subroute_{function_type}", headers={"Authorization": "Bearer valid"}, should_check_response=False)
    assert r.text == "bypassed"
