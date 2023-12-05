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
