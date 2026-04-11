from robyn.responses import RedirectResponse


def test_redirect_response_defaults():
    resp = RedirectResponse("/new-location")
    assert resp.status_code == 307
    assert resp.headers.get("Location") == "/new-location"


def test_redirect_response_301():
    resp = RedirectResponse("/permanent", status_code=301)
    assert resp.status_code == 301
    assert resp.headers.get("Location") == "/permanent"


def test_redirect_response_with_extra_headers():
    from robyn.robyn import Headers

    h = Headers({"X-Custom": "value"})
    resp = RedirectResponse("/target", headers=h)
    assert resp.headers.get("Location") == "/target"
    assert resp.headers.get("X-Custom") == "value"
