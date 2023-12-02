import pytest

from integration_tests.helpers.http_methods_helpers import get

BASE_URL = "http://127.0.0.1:8080"


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "route, text",
    [
        ("/sync/octet", "sync octet"),
        ("/async/octet", "async octet"),
        ("/sync/octet/response", "sync octet response"),
        ("/async/octet/response", "async octet response"),
    ],
)
def test_binary_output(route: str, text: str, session):
    r = get(route)
    assert r.headers.get("Content-Type") == "application/octet-stream"
    assert r.text == text
