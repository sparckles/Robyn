from urllib.parse import urlparse

import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication(session, function_type: str):
    r = get(f"/{function_type}/auth", headers={"Authorization": "Bearer valid"})
    assert r.text == "authenticated"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_valid_authentication_trailing_slash(session, function_type: str):
    r = get(f"/{function_type}/auth/", headers={"Authorization": "Bearer valid"})
    # Checks whether request is being sent to exact /trailing/ route.
    assert urlparse(r.url).path == f"/{function_type}/auth/"
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
def test_invalid_authentication_token_trailing_slash(session, function_type: str):
    r = get(
        f"/{function_type}/auth/",
        headers={"Authorization": "Bearer invalid"},
        should_check_response=False,
    )
    assert urlparse(r.url).path == f"/{function_type}/auth/"
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
def test_invalid_authentication_header_trailing_slash(session, function_type: str):
    r = get(
        f"/{function_type}/auth/",
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


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_invalid_authentication_no_token_trailing_slash(session, function_type: str):
    r = get(f"/{function_type}/auth/", should_check_response=False)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "BearerGetter"
