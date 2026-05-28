from robyn.robyn import Headers, QueryParams, Request, Url


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
    print(request.headers.get("Content-Type"))
    assert request.headers.get("Content-Type") == "application/json"
    assert request.method == "GET"


def test_request_json_accepts_bytes_body():
    request = Request(
        query_params=QueryParams(),
        headers=Headers({"Content-Type": "application/json"}),
        path_params={},
        body=b'{"hello": "world", "count": 1}',
        method="POST",
        url=Url(scheme="https", host="localhost", path="/user"),
        ip_addr=None,
        identity=None,
        form_data={},
        files={},
    )

    assert request.json() == {"hello": "world", "count": 1}
