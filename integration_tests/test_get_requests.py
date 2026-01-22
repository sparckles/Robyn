import pytest
import requests
from requests import Response

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_param(function_type: str, session):
    r = get(f"/{function_type}/param/1")
    assert r.text == "1"
    r = get(f"/{function_type}/param/12345")
    assert r.text == "12345"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_param_suffix(function_type: str, session):
    r = get(f"/{function_type}/extra/foo/1/baz")
    assert r.text == "foo/1/baz"
    r = get(f"/{function_type}/extra/foo/bar/baz")
    assert r.text == "foo/bar/baz"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_serve_html(function_type: str, session):
    def check_response(r: Response):
        assert r.text.startswith("<!DOCTYPE html>")
        assert "Hello world. How are you?" in r.text

    check_response(get(f"/{function_type}/serve/html"))


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_template(function_type: str, session):
    def check_response(r: Response):
        assert r.text.startswith("\n\n<!DOCTYPE html>")
        assert "Jinja2" in r.text
        assert "Robyn" in r.text

    check_response(get(f"/{function_type}/template"))


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_queries(function_type: str, session):
    r = get(f"/{function_type}/queries?hello=robyn")
    assert r.json() == {"hello": ["robyn"]}

    r = get(f"/{function_type}/queries")
    assert r.json() == {}


@pytest.mark.benchmark
def test_trailing_slash(session):
    r = requests.get("http://localhost:8080/trailing")  # `integration_tests#get` strips the trailing slash, tests always pass!`
    assert r.text == "Trailing slash test successful!"

    r = requests.get("http://localhost:8080/trailing/")
    assert r.text == "Trailing slash test successful!"


@pytest.mark.benchmark
@pytest.mark.parametrize("key, value", [("fakesession", "fake-cookie-session-value")])
def test_cookies(session, key, value):
    response = get("/cookie", 200)

    # Cookies should be sent via Set-Cookie header, accessible via response.cookies
    assert response.cookies[key] == value


@pytest.mark.benchmark
def test_multiple_cookies(session):
    response = get("/cookie/multiple", 200)

    assert response.cookies["session"] == "abc123"
    assert response.cookies["theme"] == "dark"


@pytest.mark.benchmark
def test_cookie_with_attributes(session):
    response = get("/cookie/attributes", 200)

    # Check the cookie value
    assert response.cookies["secure_session"] == "secret123"

    # Check the Set-Cookie header for attributes
    set_cookie_header = response.headers.get("Set-Cookie", "")
    assert "secure_session=secret123" in set_cookie_header
    assert "Path=/" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
    assert "Secure" in set_cookie_header
    assert "SameSite=Strict" in set_cookie_header
    assert "Max-Age=3600" in set_cookie_header


@pytest.mark.benchmark
def test_cookie_overwrite(session):
    response = get("/cookie/overwrite", 200)

    # Same-name cookies should be overwritten, final value should be used
    assert response.cookies["session"] == "final-value"
