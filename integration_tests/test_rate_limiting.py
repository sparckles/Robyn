from collections.abc import Callable
import pytest
from helpers.http_methods_helpers import get, post, put


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "route,method",
    [
        ("/sync/rate/get", get),
        ("/async/rate/get", get),
        ("/sync/rate/put", put),
        ("/async/rate/put", put),
        ("/sync/rate/post", post),
        ("/async/rate/post", post),
    ],
)
def test_throttling(
    route: str,
    method: Callable,
    session,
):
    r = method(route, expected_status_code=200)
    assert r.text == "OK"
    r = method(route, expected_status_code=200)
    assert r.text == "OK"
    r = method(route, expected_status_code=200)
    assert r.text == "OK"
    r = method(route, expected_status_code=429)
    assert r.text == "Rate limit exceeded"
