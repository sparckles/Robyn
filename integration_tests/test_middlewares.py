from helpers.http_methods_helpers import get


def test_middlewares(session):
    r = get("/")
    assert "before" in r.headers
    assert r.headers["before"] == "before_request"
    assert "after" in r.headers
    assert r.headers["after"] == "after_request"
