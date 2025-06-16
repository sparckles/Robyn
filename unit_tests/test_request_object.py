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
    # Test single header values
    headers = Headers({"Content-Type": "application/json", "Authorization": "Bearer token"})
    headers_dict = headers.to_dict()

    assert headers_dict["content-type"] == "application/json"
    assert headers_dict["authorization"] == "Bearer token"

    # Test with default values (Flask-style behavior)
    custom_header = headers_dict.get("x-custom", "default")
    assert custom_header == "default"

    user_agent = headers_dict.get("user-agent", "blank/None")
    assert user_agent == "blank/None"


def test_headers_to_dict_with_duplicates():
    # Test duplicate header values (joined with commas)
    headers = Headers({})
    headers.append("X-Custom", "value1")
    headers.append("X-Custom", "value2")
    headers.append("X-Custom", "value3")

    headers_dict = headers.to_dict()

    # Should join multiple values with commas (Flask-style)
    assert headers_dict["x-custom"] == "value1,value2,value3"


def test_headers_to_dict_vs_get_headers():
    # Compare to_dict() with get_headers() behavior
    headers = Headers({})
    headers.set("Content-Type", "application/json")
    headers.append("X-Custom", "value1")
    headers.append("X-Custom", "value2")

    # get_headers returns dict of lists
    headers_lists = headers.get_headers()
    assert headers_lists["content-type"] == ["application/json"]
    assert headers_lists["x-custom"] == ["value1", "value2"]

    # to_dict returns flattened dict with comma-separated values
    headers_dict = headers.to_dict()
    assert headers_dict["content-type"] == "application/json"
    assert headers_dict["x-custom"] == "value1,value2"


def test_headers_to_dict_empty():
    # Test empty headers
    headers = Headers({})
    headers_dict = headers.to_dict()

    assert headers_dict == {}
    assert headers_dict.get("any-header", "default") == "default"
