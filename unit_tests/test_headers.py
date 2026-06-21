from robyn.robyn import Headers


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
