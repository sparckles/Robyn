import pytest

from helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_middlewares(function_type: str, session):
    r = get(f"/{function_type}/middlewares")
    # We do not want the request headers to be in the response
    assert "before" not in r.headers
    assert "after" in r.headers
    assert r.headers["after"] == f"{function_type}_after_request"
    assert r.text == f"{function_type} middlewares after"
