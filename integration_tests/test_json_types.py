import pytest

from integration_tests.helpers.http_methods_helpers import json_post


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

