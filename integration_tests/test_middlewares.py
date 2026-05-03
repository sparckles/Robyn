import sys

import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_middlewares(function_type: str, session):
    r = get(f"/{function_type}/middlewares")
    headers = r.headers
    # We do not want the request headers to be in the response
    assert not headers.get("before")
    assert headers.get("after")
    assert r.headers.get("after") == f"{function_type}_after_request"
    assert r.text == f"{function_type} middlewares after"


@pytest.mark.benchmark
def test_global_middleware(session):
    r = get("/sync/global/middlewares")
    headers = r.headers
    assert headers.get("global_after")
    assert r.headers.get("global_after") == "global_after_request"
    assert r.text == "sync global middlewares"


@pytest.mark.benchmark
def test_response_in_before_middleware(session):
    r = get("/sync/middlewares/401", should_check_response=False)
    assert r.status_code == 401


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "route",
    [
        "/sync/str/const",
        "/async/str/const",
        "/sync/dict/const",
        "/async/dict/const",
        "/sync/response/const",
        "/async/response/const",
    ],
)
def test_global_middleware_applied_to_const_routes(route: str, session):
    r = get(route)
    assert r.headers.get("global_after") == "global_after_request", f"Global after-request middleware was not applied to const route {route}"


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "function_type, expected",
    [
        pytest.param(
            "async",
            "set-in-before",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 11),
                reason="Sharing ContextVar writes across async middleware phases requires loop.create_task(context=...), which is Python 3.11+ (see #1380).",
            ),
        ),
        ("sync", "set-in-sync-before"),
    ],
)
def test_contextvars_propagate_across_hooks(function_type: str, expected: str, session):
    """Regression test for #1380: `contextvars.ContextVar` writes in
    `before_request` must be visible to the route handler and to
    `after_request`. Each request gets a fresh shared context.
    """
    r = get(f"/{function_type}/contextvars/route")
    assert r.text == expected, "Route handler did not observe ContextVar set in before_request"
    assert r.headers.get("x-ctxvar-after") == expected, "after_request did not observe ContextVar set in before_request"
