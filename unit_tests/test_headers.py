from robyn.robyn import Headers, QueryParams


def test_to_dict_returns_flat_dict():
    headers = Headers({"Content-Type": "application/json"})
    result = headers.to_dict()

    assert isinstance(result, dict)
    # keys are normalised to lowercase, like the rest of the Headers API
    assert result["content-type"] == "application/json"


def test_to_dict_joins_duplicate_values():
    headers = Headers({"X-Forwarded-For": ["10.0.0.1", "10.0.0.2"]})
    result = headers.to_dict()

    assert result["x-forwarded-for"] == "10.0.0.1, 10.0.0.2"


def test_to_dict_supports_get_with_default():
    # The whole point of #1099: a real dict so callers can supply a default
    # for a missing header instead of always getting None.
    headers = Headers({"Content-Type": "application/json"})
    result = headers.to_dict()

    assert result.get("content-type", "text/plain") == "application/json"
    assert result.get("x-missing", "fallback") == "fallback"


def test_to_dict_empty_headers():
    headers = Headers(None)
    assert headers.to_dict() == {}


# --- dict-like accessors (#1192) -------------------------------------------


def test_headers_keys_values_items():
    headers = Headers({"Content-Type": "application/json", "Accept": "text/html"})

    assert sorted(headers.keys()) == ["accept", "content-type"]
    assert sorted(headers.values()) == ["application/json", "text/html"]
    assert sorted(headers.items()) == [
        ("accept", "text/html"),
        ("content-type", "application/json"),
    ]


def test_headers_items_use_last_value():
    headers = Headers({"X-Trace": ["a", "b"]})
    # keys()/values()/items() collapse to the last value, like get()
    assert headers.get("X-Trace") == "b"
    assert headers.items() == [("x-trace", "b")]
    assert headers.values() == ["b"]


def test_headers_multi_items_preserves_duplicates():
    headers = Headers({"X-Trace": ["a", "b"]})
    assert sorted(headers.multi_items()) == [("x-trace", "a"), ("x-trace", "b")]


def test_query_params_keys_values_items():
    params = QueryParams()
    params.set("q", "robyn")
    params.set("page", "1")

    assert sorted(params.keys()) == ["page", "q"]
    assert sorted(params.values()) == ["1", "robyn"]
    assert sorted(params.items()) == [("page", "1"), ("q", "robyn")]


def test_query_params_multi_items_preserves_duplicates():
    params = QueryParams()
    params.set("tag", "a")
    params.set("tag", "b")

    # items() collapses to the last value; multi_items() keeps every value
    assert params.items() == [("tag", "b")]
    assert sorted(params.multi_items()) == [("tag", "a"), ("tag", "b")]
