from collections.abc import Callable
import pytest
from integration_tests.helpers.http_methods_helpers import get, post, put


@pytest.mark.benchmark
@pytest.mark.usefixtures("session")
@pytest.mark.parametrize(
    "route,method",
    [
        ("/sync/get/no_dec", get),
        ("/async/get/no_dec", get),
        ("/sync/put/no_dec", put),
        ("/async/put/no_dec", put),
        ("/sync/post/no_dec", post),
        ("/async/post/no_dec", post),
    ],
)
def test_exception_handling(route: str, method: Callable):
    r = method(route, expected_status_code=200)
    assert r.text == "Success!"
