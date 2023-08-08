# Test the routes with:
# - the GET method
# - most common return types
# - sync and async

from typing import Optional

import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "route,expected_text,expected_header_key,expected_header_value",
    [
        ("/sync/str", "sync str get", None, None),
        ("/sync/dict", "sync dict get", "sync", "dict"),
        ("/sync/response", "sync response get", "sync", "response"),
        ("/sync/str/const", "sync str const get", None, None),
        ("/sync/dict/const", "sync dict const get", "sync_const", "dict"),
        ("/sync/response/const", "sync response const get", "sync_const", "response"),
        ("/async/str", "async str get", None, None),
        ("/async/dict", "async dict get", "async", "dict"),
        ("/async/response", "async response get", "async", "response"),
        ("/async/str/const", "async str const get", None, None),
        ("/async/dict/const", "async dict const get", "async_const", "dict"),
        (
            "/async/response/const",
            "async response const get",
            "async_const",
            "response",
        ),
    ],
)
def test_basic_get(
    route: str,
    expected_text: str,
    expected_header_key: Optional[str],
    expected_header_value: Optional[str],
    session,
):
    res = get(route)
    assert res.text == expected_text
    if expected_header_key is not None:
        assert expected_header_key in res.headers
        assert res.headers[expected_header_key] == expected_header_value


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "route, expected_json",
    [
        ("/sync/json", {"sync json get": "json"}),
        ("/async/json", {"async json get": "json"}),
        ("/sync/json/const", {"sync json const get": "json"}),
        ("/async/json/const", {"async json const get": "json"}),
    ],
)
def test_json_get(route: str, expected_json: dict, session):
    res = get(route)
    for key in expected_json.keys():
        assert key in res.json()
        assert res.json()[key] == expected_json[key]


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "route, expected_json",
    [
        (
            "/sync/http/param",
            {
                "method": "GET",
                "url": {
                    "host": "127.0.0.1:8080",
                    "path": "/sync/http/param",
                    "scheme": "http",
                },
            },
        ),
        (
            "/async/http/param",
            {
                "method": "GET",
                "url": {
                    "host": "127.0.0.1:8080",
                    "path": "/async/http/param",
                    "scheme": "http",
                },
            },
        ),
    ],
)
def test_http_request_info_get(route: str, expected_json: dict, session):
    res = get(route)
    for key in expected_json.keys():
        assert key in res.json()
        assert res.json()[key] == expected_json[key]
