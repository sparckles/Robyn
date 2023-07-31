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
    test_rate_limiting_session,
):
    BASE_URL = "http://127.0.0.1:8082"
    r = method(route, expected_status_code=200, base_url=BASE_URL)
    assert r.text == "OK"
    r = method(route, expected_status_code=200, base_url=BASE_URL)
    assert r.text == "OK"
    r = method(route, expected_status_code=200, base_url=BASE_URL)
    assert r.text == "OK"
    r = method(route, expected_status_code=429, base_url=BASE_URL)
    assert r.text == "Rate limit exceeded"
