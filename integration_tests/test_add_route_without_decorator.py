from collections.abc import Callable

import pytest

from integration_tests.helpers.http_methods_helpers import get, post, put
from robyn.testing import TestClient as RobynTestClient


@pytest.fixture
def client():
    """Use the existing integration app without launching its server."""
    from integration_tests.base_routes import app

    with RobynTestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "route,method",
    [
        ("/sync/get/no_dec", "get"),
        ("/async/get/no_dec", "get"),
        ("/sync/put/no_dec", "put"),
        ("/async/put/no_dec", "put"),
        ("/sync/post/no_dec", "post"),
        ("/async/post/no_dec", "post"),
    ],
)
def test_add_route_without_decorator(client: RobynTestClient, route: str, method: str):
    response = getattr(client, method)(route)
    assert response.status_code == 200
    assert response.text == "Success!"


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
    # Keep the HTTP benchmarks and their Rust routing/middleware/header coverage.
    # TestClient dispatches in Python and skips after middleware for bare strings.
    r = method(route, expected_status_code=200)
    assert r.text == "Success!"
