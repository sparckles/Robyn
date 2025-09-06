import pytest
import json

from integration_tests.helpers.http_methods_helpers import post


@pytest.mark.parametrize(
    "route, body, expected_result",
    [
        ("/sync/request_json", '{"hello": "world"}', "<class 'dict'>"),
        ("/sync/request_json/key", '{"key": "world"}', "world"),
        ("/sync/request_json", '{"hello": "world"', "None"),
        ("/async/request_json", '{"hello": "world"}', "<class 'dict'>"),
        ("/async/request_json", '{"hello": "world"', "None"),
    ],
)
def test_request(route, body, expected_result):
    res = post(route, body)
    assert res.text == expected_result


# Tests for JSON array handling (Issue #1145)

@pytest.mark.parametrize("endpoint", ["/sync/request_json_array", "/async/request_json_array"])
def test_json_array_parsing(endpoint):
    """Test that JSON arrays are properly parsed as Python lists"""
    test_data = ["google_docs", "notion"]
    response = post(endpoint, json=test_data)
    
    assert response.status_code == 200
    result = response.json()
    
    # Check that the array was parsed as a list
    assert result["type"] == "list"
    assert result["length"] == 2
    assert result["data"] == ["google_docs", "notion"]


@pytest.mark.parametrize("endpoint", ["/sync/request_json_array", "/async/request_json_array"])
def test_json_object_with_array(endpoint):
    """Test that JSON object containing arrays is properly parsed"""
    test_data = {
        "sources": ["google_docs", "notion"]
    }
    response = post(endpoint, json=test_data)
    
    assert response.status_code == 200
    result = response.json()
    
    # Check that the object was parsed as a dict
    assert result["type"] == "dict"
    assert result["data"]["sources"] == ["google_docs", "notion"]
    # Verify that nested array is properly parsed as a list, not string
    assert isinstance(result["data"]["sources"], list)


@pytest.mark.parametrize("endpoint", ["/sync/request_json_types", "/async/request_json_types"])
def test_json_various_types(endpoint):
    """Test various JSON types are properly handled"""
    
    # Test cases: (json_data, expected_type, expected_checks)
    test_cases = [
        # Array (the main issue from #1145)
        (["item1", "item2"], "list", {"is_list": True, "is_dict": False}),
        # Object
        ({"key": "value"}, "dict", {"is_dict": True, "is_list": False}),
        # String
        ("hello world", "str", {"is_string": True, "is_dict": False, "is_list": False}),
        # Number (int)
        (42, "int", {"is_number": True, "is_string": False, "is_list": False}),
        # Number (float) 
        (3.14, "float", {"is_number": True, "is_string": False, "is_list": False}),
        # Boolean
        (True, "bool", {"is_bool": True, "is_number": False, "is_string": False}),
        # Null
        (None, "NoneType", {"is_none": True, "is_bool": False, "is_string": False}),
        # Empty array
        ([], "list", {"is_list": True, "is_dict": False}),
        # Empty object
        ({}, "dict", {"is_dict": True, "is_list": False}),
    ]
    
    for test_data, expected_type, expected_checks in test_cases:
        response = post(endpoint, json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        
        # Check type
        assert result["type"] == expected_type, f"Expected {expected_type} but got {result['type']} for data {test_data}"
        
        # Check data integrity
        assert result["data"] == test_data, f"Data integrity failed for {test_data}"
        
        # Check specific type flags
        for check_key, expected_value in expected_checks.items():
            assert result[check_key] == expected_value, f"Check {check_key} failed for {test_data}"


def test_original_issue_1145_case():
    """Test the exact case described in issue #1145"""
    payload = {
        "sources": ["google_docs", "notion"]  
    }
    
    # Test both sync and async endpoints
    for endpoint in ["/sync/request_json_types", "/async/request_json_types"]:
        response = post(endpoint, json=payload)
        
        assert response.status_code == 200
        result = response.json()
        
        # The original issue was that arrays were returned as strings
        # Now they should be properly parsed as lists
        assert result["is_dict"] == True
        assert result["data"]["sources"] == ["google_docs", "notion"]
        assert isinstance(result["data"]["sources"], list)  # This was failing before the fix
        
        # Verify it's not a string representation of an array
        assert result["data"]["sources"] != '["google_docs","notion"]'
        assert result["data"]["sources"] != "['google_docs', 'notion']"


@pytest.mark.parametrize("endpoint", ["/sync/request_json_array", "/async/request_json_array"])  
def test_complex_nested_structures(endpoint):
    """Test complex nested array structures"""
    test_data = [
        {"id": 1, "sources": ["google", "bing"]},
        {"id": 2, "sources": ["yahoo", "duckduckgo"]},
        ["item1", "item2", ["nested", "array"]]
    ]
    
    response = post(endpoint, json=test_data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["type"] == "list" 
    assert result["length"] == 3
    assert result["data"] == test_data
    
    # Verify nested structures are preserved
    assert result["data"][0]["sources"] == ["google", "bing"]
    assert result["data"][2][2] == ["nested", "array"]
