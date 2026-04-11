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


def test_headers_to_dict():
    headers = Headers({"Content-Type": "application/json", "Authorization": "Bearer token"})
    headers_dict = headers.to_dict()
    assert headers_dict["content-type"] == "application/json"
    assert headers_dict["authorization"] == "Bearer token"
    custom_header = headers_dict.get("x-custom", "default")
    assert custom_header == "default"


def test_headers_to_dict_with_duplicates():
    headers = Headers({})
    headers.append("X-Custom", "value1")
    headers.append("X-Custom", "value2")
    headers.append("X-Custom", "value3")
    headers_dict = headers.to_dict()
    assert headers_dict["x-custom"] == "value1,value2,value3"


def test_headers_get_headers():
    headers = Headers({})
    headers.set("Content-Type", "application/json")
    headers.append("X-Custom", "value1")
    headers.append("X-Custom", "value2")
    headers_lists = headers.get_headers()
    assert headers_lists["content-type"] == ["application/json"]
    assert headers_lists["x-custom"] == ["value1", "value2"]


def test_headers_to_dict_empty():
    headers = Headers({})
    headers_dict = headers.to_dict()
    assert headers_dict == {}
    assert headers_dict.get("any-header", "default") == "default"
