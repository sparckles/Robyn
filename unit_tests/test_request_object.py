from robyn.robyn import Headers, QueryParams, Request, Url
import pytest


def test_request_object():
    url = Url(
        scheme="https",
        host="localhost",
        path="/user",
    )
    request = Request(
        query_params=QueryParams(),
        headers=Headers({"Content-Type": "application/json"}),
        path_params={},
        body="",
        method="GET",
        url=url,
        ip_addr=None,
        identity=None,
        form_data={},
        files={},
    )

    assert request.url.scheme == "https"
    assert request.url.host == "localhost"
    assert request.headers.get("Content-Type") == "application/json"
    assert request.method == "GET"


def test_request_object_body_json():
    url = Url(
        scheme="https",
        host="localhost",
        path="/user",
    )
    request = Request(
        query_params=QueryParams(),
        headers=Headers({"Content-Type": "application/json"}),
        path_params={},
        body='{"key": "value"}',
        method="POST",
        url=url,
        ip_addr=None,
        identity=None,
        form_data={},
        files={},
    )

    assert request.json() == {"key": "value"}

    request = Request(
        query_params=QueryParams(),
        headers=Headers({"Content-Type": "application/json"}),
        path_params={},
        body="",
        method="POST",
        url=url,
        ip_addr=None,
        identity=None,
        form_data={},
        files={},
    )

    pytest.raises(ValueError, request.json)
