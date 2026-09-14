import json

import pytest

from robyn.robyn import Headers, Response
from robyn.router import Router


@pytest.fixture
def router():
    return Router()


def _body(response: Response) -> bytes:
    description = response.description
    return description if isinstance(description, bytes) else description.encode()


def test_tuple_with_dict_body_is_json(router):
    response = router._format_tuple_response(({"key": "value"}, {}, 201))
    assert response.status_code == 201
    assert json.loads(_body(response)) == {"key": "value"}
    assert response.headers.get("Content-Type") == "application/json"


def test_tuple_with_list_body_is_json(router):
    response = router._format_tuple_response(([1, 2], {}, 200))
    assert json.loads(_body(response)) == [1, 2]
    assert response.headers.get("Content-Type") == "application/json"


def test_tuple_with_str_body_is_text(router):
    response = router._format_tuple_response(("created", {"X-Custom": "yes"}, 201))
    assert response.status_code == 201
    assert _body(response) == b"created"
    assert response.headers.get("Content-Type") == "text/plain"
    assert response.headers.get("X-Custom") == "yes"


def test_tuple_with_bytes_body_is_octet_stream(router):
    response = router._format_tuple_response((b"\x00\x01", {}, 206))
    assert _body(response) == b"\x00\x01"
    assert response.headers.get("Content-Type") == "application/octet-stream"


def test_tuple_headers_may_be_a_headers_object(router):
    response = router._format_tuple_response(("ok", Headers({"X-Custom": "yes"}), 202))
    assert response.status_code == 202
    assert response.headers.get("X-Custom") == "yes"


def test_tuple_headers_override_content_type(router):
    response = router._format_tuple_response(({"detail": "bad"}, {"Content-Type": "application/problem+json"}, 400))
    assert response.status_code == 400
    assert response.headers.get("Content-Type") == "application/problem+json"


def test_tuple_with_response_body_keeps_its_headers_and_takes_the_status(router):
    inner = Response(status_code=200, headers=Headers({"Content-Type": "text/html"}), description="<b>x</b>")
    response = router._format_tuple_response((inner, {"X-Custom": "yes"}, 418))
    assert response.status_code == 418
    assert _body(response) == b"<b>x</b>"
    assert response.headers.get("Content-Type") == "text/html"
    assert response.headers.get("X-Custom") == "yes"


def test_tuple_must_have_three_elements(router):
    with pytest.raises(ValueError):
        router._format_tuple_response(({"key": "value"}, 201))
