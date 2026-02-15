import pytest

from integration_tests.helpers.http_methods_helpers import get, json_post


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_integer_type_preserved(function_type: str, session):
    """Test that integer values in JSON are preserved as integers, not strings"""
    json_data = {"lid": 570, "count": 42}
    res = json_post(f"/{function_type}/request_json/types", json_data=json_data)
    result = res.json()

    assert result["lid"]["value"] == 570
    assert result["lid"]["type"] == "int"
    assert result["count"]["value"] == 42
    assert result["count"]["type"] == "int"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_null_type_preserved(function_type: str, session):
    """Test that null values in JSON are preserved as None, not string 'null'"""
    json_data = {"start": None, "end": None}
    res = json_post(f"/{function_type}/request_json/types", json_data=json_data)
    result = res.json()

    assert result["start"]["value"] is None
    assert result["start"]["type"] == "NoneType"
    assert result["end"]["value"] is None
    assert result["end"]["type"] == "NoneType"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_boolean_type_preserved(function_type: str, session):
    """Test that boolean values in JSON are preserved as booleans, not strings"""
    json_data = {"active": True, "deleted": False}
    res = json_post(f"/{function_type}/request_json/types", json_data=json_data)
    result = res.json()

    assert result["active"]["value"] is True
    assert result["active"]["type"] == "bool"
    assert result["deleted"]["value"] is False
    assert result["deleted"]["type"] == "bool"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_float_type_preserved(function_type: str, session):
    """Test that float values in JSON are preserved as floats"""
    json_data = {"price": 19.99, "rate": 0.15}
    res = json_post(f"/{function_type}/request_json/types", json_data=json_data)
    result = res.json()

    assert result["price"]["value"] == 19.99
    assert result["price"]["type"] == "float"
    assert result["rate"]["value"] == 0.15
    assert result["rate"]["type"] == "float"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_string_type_preserved(function_type: str, session):
    """Test that string values in JSON remain strings"""
    json_data = {"field_name": "mobile", "field_value": "111000111"}
    res = json_post(f"/{function_type}/request_json/types", json_data=json_data)
    result = res.json()

    assert result["field_name"]["value"] == "mobile"
    assert result["field_name"]["type"] == "str"
    assert result["field_value"]["value"] == "111000111"
    assert result["field_value"]["type"] == "str"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_array_type_preserved(function_type: str, session):
    """Test that array values in JSON are preserved as lists"""
    json_data = {"items": [1, 2, 3], "tags": ["a", "b"]}
    res = json_post(f"/{function_type}/request_json/types", json_data=json_data)
    result = res.json()

    assert result["items"]["value"] == [1, 2, 3]
    assert result["items"]["type"] == "list"
    assert result["tags"]["value"] == ["a", "b"]
    assert result["tags"]["type"] == "list"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_nested_object_type_preserved(function_type: str, session):
    """Test that nested object values in JSON are preserved as dicts"""
    json_data = {"user": {"name": "John", "age": 30}}
    res = json_post(f"/{function_type}/request_json/types", json_data=json_data)
    result = res.json()

    assert result["user"]["value"] == {"name": "John", "age": 30}
    assert result["user"]["type"] == "dict"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_mixed_types_preserved(function_type: str, session):
    """Test the exact scenario from the bug report - mixed types in one request"""
    json_data = {
        "lid": 570,
        "start": None,
        "field_name": "mobile",
        "field_value": "111000111",
    }
    res = json_post(f"/{function_type}/request_json/types", json_data=json_data)
    result = res.json()

    # Integer should remain integer (not become "570")
    assert result["lid"]["value"] == 570
    assert result["lid"]["type"] == "int"

    # None should remain None (not become "null")
    assert result["start"]["value"] is None
    assert result["start"]["type"] == "NoneType"

    # Strings should remain strings
    assert result["field_name"]["value"] == "mobile"
    assert result["field_name"]["type"] == "str"
    assert result["field_value"]["value"] == "111000111"
    assert result["field_value"]["type"] == "str"


# ===== Top-level JSON Array Parsing Tests (Issue #1145) =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_top_level_array_of_strings(function_type: str, session):
    """Test that request.json() handles a top-level array of strings (exact scenario from #1145)"""
    json_data = ["google_docs", "notion"]
    res = json_post(f"/{function_type}/request_json/array", json_data=json_data)
    result = res.json()

    assert result["type"] == "list"
    assert result["parsed"] == ["google_docs", "notion"]


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_top_level_array_of_objects(function_type: str, session):
    """Test that request.json() handles a top-level array of objects"""
    json_data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    res = json_post(f"/{function_type}/request_json/array", json_data=json_data)
    result = res.json()

    assert result["type"] == "list"
    assert result["parsed"] == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_top_level_empty_array(function_type: str, session):
    """Test that request.json() handles an empty top-level array"""
    json_data = []
    res = json_post(f"/{function_type}/request_json/array", json_data=json_data)
    result = res.json()

    assert result["type"] == "list"
    assert result["parsed"] == []


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_top_level_array_of_mixed_types(function_type: str, session):
    """Test that request.json() handles a top-level array with mixed types"""
    json_data = [1, "two", True, None, {"key": "value"}]
    res = json_post(f"/{function_type}/request_json/array", json_data=json_data)
    result = res.json()

    assert result["type"] == "list"
    assert result["parsed"] == [1, "two", True, None, {"key": "value"}]


# ===== JSON List Serialization Tests (Issue #1300) =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_list_response_serialization(function_type: str, session):
    """Test that returning a list from a handler is properly serialized as JSON"""
    res = get(f"/{function_type}/json/list")

    # Check content type is application/json
    assert res.headers["content-type"] == "application/json"

    # Check that response is valid JSON (not Python str representation)
    result = res.json()
    assert isinstance(result, list)
    assert len(result) == 3

    # Verify the data structure and types are correct
    assert result[0] == {"id": 1, "title": "First Post", "published": True}
    assert result[1] == {"id": 2, "title": "Draft Post", "published": False}
    assert result[2] == {"id": 3, "title": "Latest Post", "published": True}

    # Verify booleans are proper JSON booleans (true/false), not Python (True/False)
    # This is implicitly tested by res.json() succeeding, but let's verify the raw response too
    assert "true" in res.text.lower()
    assert "false" in res.text.lower()
    assert "True" not in res.text  # Python boolean should not appear
    assert "False" not in res.text


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_empty_list_response_serialization(function_type: str, session):
    """Test that returning an empty list is properly serialized as JSON"""
    res = get(f"/{function_type}/json/list/empty")

    assert res.headers["content-type"] == "application/json"
    result = res.json()
    assert result == []
    assert res.text == "[]"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_list_primitives_response_serialization(function_type: str, session):
    """Test that a list of primitives is properly serialized as JSON"""
    res = get(f"/{function_type}/json/list/primitives")

    assert res.headers["content-type"] == "application/json"
    result = res.json()
    assert result == [1, 2, 3, "four", True, None]


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_json_dict_response_auto_serialization(function_type: str, session):
    """Test that returning a dict from a handler is properly auto-serialized as JSON"""
    res = get(f"/{function_type}/json/dict")

    assert res.headers["content-type"] == "application/json"
    result = res.json()
    assert result["message"] == f"{function_type} dict"
    assert result["count"] == 42
    assert result["active"] is True
