from collections.abc import Callable
import pytest
from integration_tests.helpers.http_methods_helpers import get, post, put


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "route,method",
    [
        ("/sync/exception/get", get),
        ("/async/exception/get", get),
        ("/sync/exception/put", put),
        ("/async/exception/put", put),
        ("/sync/exception/post", post),
        ("/async/exception/post", post),
    ],
)
def test_exception_handling(
    route: str,
    method: Callable,
    session,
):
    r = method(route, expected_status_code=500)
    assert r.text == "error msg: value error"
