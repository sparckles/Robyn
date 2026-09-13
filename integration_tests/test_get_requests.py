import json

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


@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize(
    "query, expected",
    [
        ("v=a%20b", {"v": ["a b"]}),
        ("first%20name=Ada+Lovelace", {"first name": ["Ada Lovelace"]}),
        ("v=a+b&plus%2Bkey=%2B", {"v": ["a b"], "plus+key": ["+"]}),
        ("a%26b=x%3Dy%26z%3F%23", {"a&b": ["x=y&z?#"]}),
        ("%E5%90%8D=%E6%9D%B1%E4%BA%AC%F0%9F%98%80", {"名": ["東京😀"]}),
        ("v=%2520%252B", {"v": ["%20%2B"]}),
        ("v=first&v=second&v=second", {"v": ["first", "second", "second"]}),
        ("empty=&flag", {"empty": [""], "flag": [""]}),
        ("=first&=second", {"": ["first", "second"]}),
        ("&v=one&&v=two&", {"v": ["one", "two"]}),
        ("=first&&=second", {"": ["first", "second"]}),
        ("v=%FF", {"v": ["\ufffd"]}),
    ],
)
def test_queries_decode_parameters(function_type: str, query: str, expected: dict, session):
    response = get(f"/{function_type}/queries?{query}")
    assert json.loads(response.content) == expected


def test_decoded_query_accessors_preserve_duplicate_values(session):
    response = get("/queries/accessors?first%20name=Ada+Lovelace&first+name=Grace%2BHopper&first%20name=Grace%2BHopper")
    values = ["Ada Lovelace", "Grace+Hopper", "Grace+Hopper"]
    assert response.json() == {
        "get": values[-1],
        "get_first": values[0],
        "get_all": values,
        "items": {"first name": values[-1]},
        "to_dict": {"first name": values},
    }


@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize(
    "encoded, expected",
    [
        ("attempt%3A1", "attempt:1"),
        ("a%20b", "a b"),
        ("a+b", "a+b"),
        ("a%2Bb", "a+b"),
        ("a%2Fb", "a/b"),
        ("%252F", "%2F"),
        ("%E6%9D%B1%E4%BA%AC%F0%9F%98%80", "東京😀"),
        ("%FF", "\ufffd"),
    ],
)
def test_path_parameters_decode_after_matching(function_type: str, encoded: str, expected: str, session):
    response = get(f"/{function_type}/param/{encoded}")
    assert response.content.decode("utf-8") == expected


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_catchall_path_parameters_decode_after_matching(function_type: str, session):
    response = get(f"/{function_type}/extra/a%2Fb/c%20d+e/%252F")
    assert response.content.decode("utf-8") == "a/b/c d+e/%2F"


@pytest.mark.parametrize("encoded, expected", [("a%2Fb", "a/b"), ("a+b", "a+b"), ("%252F", "%2F"), ("%E6%9D%B1%E4%BA%AC", "東京")])
def test_middleware_and_handler_receive_decoded_path_parameters(encoded: str, expected: str, session):
    path = f"/params/decoded/{encoded}"
    response = get(path)
    assert response.json() == {"before": expected, "handler": expected, "path": path}


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
