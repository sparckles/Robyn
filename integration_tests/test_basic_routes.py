# Test the routes with:
# - the GET method
# - most common return types
# - sync and async
# The syntax for the routes dict is `route: (expected_body, expected_header_key, expected_header_value)`

from utils import get

SYNC_ROUTES = {
    "/sync/str": ("sync str", None, None),
    "/sync/dict": ("sync dict", "sync", "dict"),
    "/sync/response": ("sync response", "sync", "response"),
}

SYNC_ROUTES_CONST = {
    "/sync/str/const": ("sync str const", None, None),
    "/sync/dict/const": ("sync dict const", "sync_const", "dict"),
    "/sync/response/const": ("sync response const", "sync_const", "response"),
}

ASYNC_ROUTES = {
    "/async/str": ("async str", None, None),
    "/async/dict": ("async dict", "async", "dict"),
    "/async/response": ("async response", "async", "response"),
}

ASYNC_ROUTES_CONST = {
    "/async/str/const": ("async str const", None, None),
    "/async/dict/const": ("async dict const", "async_const", "dict"),
    "/async/response/const": ("async response const", "async_const", "response"),
}

JSON_ROUTES = {
    "/sync/json": {"sync json": "json"},
    "/async/json": {"async json": "json"},
}

JSON_ROUTES_CONST = {
    "/sync/json/const": {"sync json const": "json"},
    "/async/json/const": {"async json const": "json"},
}


def test_sync_get(session):
    routes = SYNC_ROUTES
    routes.update(SYNC_ROUTES_CONST)
    for route, expected in routes.items():
        res = get(route)
        assert res.text == expected[0] + " get"
        if expected[1] is not None:
            assert expected[1] in res.headers
            assert res.headers[expected[1]] == expected[2]


def test_async_get(session):
    routes = ASYNC_ROUTES
    routes.update(ASYNC_ROUTES_CONST)
    for route, expected in routes.items():
        res = get(route)
        assert res.text == expected[0] + " get"
        if expected[1] is not None:
            assert expected[1] in res.headers
            assert res.headers[expected[1]] == expected[2]


def test_json_get(session):
    routes = JSON_ROUTES
    routes.update(JSON_ROUTES_CONST)
    for route, expected in routes.items():
        res = get(route)
        for key in expected.keys():
            assert key + " get" in res.json()
            assert res.json()[key + " get"] == expected[key]
