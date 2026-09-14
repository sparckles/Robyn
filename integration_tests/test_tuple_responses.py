from integration_tests.helpers.http_methods_helpers import get


def test_tuple_dict_body(session):
    r = get("/tuple/dict", expected_status_code=201)
    assert r.json() == {"key": "value"}
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["X-Custom"] == "yes"


def test_tuple_str_body_with_headers_object(session):
    r = get("/tuple/str", expected_status_code=201)
    assert r.text == "created"
    assert r.headers["Content-Type"] == "text/plain"
    assert r.headers["X-Custom"] == "yes"


def test_tuple_bytes_body(session):
    r = get("/tuple/bytes", expected_status_code=206)
    assert r.content == b"\x00\x01"
    assert r.headers["Content-Type"] == "application/octet-stream"


def test_tuple_response_body_keeps_headers_and_takes_status(session):
    r = get("/tuple/response", expected_status_code=418)
    assert r.text == "<b>x</b>"
    assert r.headers["Content-Type"] == "text/html"
    assert r.headers["X-Custom"] == "yes"


def test_tuple_headers_override_content_type(session):
    r = get("/tuple/content_type", expected_status_code=400)
    assert r.json() == {"detail": "bad"}
    assert r.headers["Content-Type"] == "application/problem+json"
