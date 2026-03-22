import importlib.util

import pytest
import requests

from integration_tests.helpers.http_methods_helpers import json_post

BASE_URL = "http://127.0.0.1:8080"

_HAS_PYDANTIC = importlib.util.find_spec("pydantic") is not None

pytestmark = pytest.mark.skipif(not _HAS_PYDANTIC, reason="pydantic not installed")


def _raw_post(endpoint: str, data: str, content_type: str = "application/json") -> requests.Response:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    return requests.post(url, data=data, headers={"Content-Type": content_type})


# ===== Valid Pydantic Body =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_valid_user_all_fields(function_type: str, session):
    """All fields provided explicitly — every field value must round-trip correctly."""
    json_data = {"name": "Alice", "email": "alice@example.com", "age": 30, "active": False}
    res = json_post(f"/{function_type}/pydantic/user", json_data=json_data)
    result = res.json()

    assert result["name"] == "Alice"
    assert result["email"] == "alice@example.com"
    assert result["age"] == 30
    assert result["active"] is False


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_default_field_applied(function_type: str, session):
    """Omitting 'active' should use the model default (True) and the handler must see it."""
    json_data = {"name": "Bob", "email": "bob@example.com", "age": 25}
    res = json_post(f"/{function_type}/pydantic/user", json_data=json_data)
    result = res.json()

    assert result["name"] == "Bob"
    assert result["email"] == "bob@example.com"
    assert result["age"] == 25
    assert result["active"] is True


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_string_to_int_coercion(function_type: str, session):
    """Pydantic v2 in lax mode (default) coerces '30' string to int 30."""
    json_data = {"name": "Coerce", "email": "c@test.com", "age": "30"}
    res = json_post(f"/{function_type}/pydantic/user", json_data=json_data)
    result = res.json()

    assert result["name"] == "Coerce"
    assert result["age"] == 30
    assert isinstance(result["age"], int)


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_extra_fields_ignored(function_type: str, session):
    """Extra fields not in the model should be silently ignored (pydantic v2 default)."""
    json_data = {"name": "Eve", "email": "eve@example.com", "age": 28, "extra_field": "should_be_ignored", "another": 99}
    res = json_post(f"/{function_type}/pydantic/user", json_data=json_data)
    result = res.json()

    assert result["name"] == "Eve"
    assert result["age"] == 28
    assert "extra_field" not in result
    assert "another" not in result


# ===== Invalid Pydantic Body — error structure verification =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_missing_single_required_field(function_type: str, session):
    """Missing 'age' should produce exactly one error with correct loc, type, and msg."""
    json_data = {"name": "Charlie", "email": "charlie@example.com"}
    res = json_post(
        f"/{function_type}/pydantic/user",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"

    errors = result["detail"]
    assert isinstance(errors, list)
    assert len(errors) == 1

    err = errors[0]
    assert err["loc"] == ["age"]
    assert err["type"] == "missing"
    assert "required" in err["msg"].lower()


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_missing_all_required_fields(function_type: str, session):
    """Sending {} should produce errors for all 3 required fields (name, email, age)."""
    res = json_post(
        f"/{function_type}/pydantic/user",
        json_data={},
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"

    errors = result["detail"]
    assert isinstance(errors, list)
    error_fields = {tuple(e["loc"]) for e in errors}
    assert ("name",) in error_fields
    assert ("email",) in error_fields
    assert ("age",) in error_fields

    for err in errors:
        assert err["type"] == "missing"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_wrong_type_error_detail(function_type: str, session):
    """Wrong type should produce error with correct loc and a meaningful msg."""
    json_data = {"name": "Diana", "email": "diana@example.com", "age": "not_a_number"}
    res = json_post(
        f"/{function_type}/pydantic/user",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"

    errors = result["detail"]
    age_errors = [e for e in errors if e["loc"] == ["age"]]
    assert len(age_errors) == 1
    assert "int" in age_errors[0]["type"]
    assert "input" in age_errors[0]
    assert age_errors[0]["input"] == "not_a_number"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_multiple_type_errors(function_type: str, session):
    """Multiple fields with wrong types should each produce their own error."""
    json_data = {"name": 12345, "email": True, "age": "bad"}
    res = json_post(
        f"/{function_type}/pydantic/user",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    error_locs = {tuple(e["loc"]) for e in result["detail"]}
    assert ("name",) in error_locs
    assert ("email",) in error_locs
    assert ("age",) in error_locs


# ===== Malformed / edge-case bodies =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_invalid_json_syntax(function_type: str, session):
    """Completely invalid JSON should return 422 with 'Invalid request body' error."""
    res = _raw_post(f"/{function_type}/pydantic/user", data="not json at all {{{")
    assert res.status_code == 422
    result = res.json()
    assert "error" in result


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_empty_body(function_type: str, session):
    """Empty body should return 422."""
    res = _raw_post(f"/{function_type}/pydantic/user", data="")
    assert res.status_code == 422
    result = res.json()
    assert "error" in result


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_json_array_body(function_type: str, session):
    """A JSON array instead of an object should return 422."""
    res = _raw_post(f"/{function_type}/pydantic/user", data='[{"name": "X"}]')
    assert res.status_code == 422


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_null_body(function_type: str, session):
    """JSON null body should return 422."""
    res = _raw_post(f"/{function_type}/pydantic/user", data="null")
    assert res.status_code == 422


# ===== Pydantic + Request object =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_with_request_object(function_type: str, session):
    """Handler receiving both Request and Pydantic model must see both correctly."""
    json_data = {"name": "Frank", "email": "frank@example.com", "age": 35}
    res = json_post(f"/{function_type}/pydantic/user_with_request", json_data=json_data)
    result = res.json()

    assert result["method"] == "POST"
    assert result["name"] == "Frank"
    assert result["email"] == "frank@example.com"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_with_request_validation_still_works(function_type: str, session):
    """Validation must still trigger 422 even when Request is in the signature."""
    json_data = {"name": "Frank"}  # missing email and age
    res = json_post(
        f"/{function_type}/pydantic/user_with_request",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"
    error_fields = {tuple(e["loc"]) for e in result["detail"]}
    assert ("email",) in error_fields
    assert ("age",) in error_fields


# ===== Nested Pydantic Models =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_nested_model_valid(function_type: str, session):
    """Valid nested model should be parsed and accessible through the parent."""
    json_data = {
        "name": "Grace",
        "email": "grace@example.com",
        "address": {"street": "123 Main St", "city": "Springfield", "zip_code": "62701"},
    }
    res = json_post(f"/{function_type}/pydantic/nested", json_data=json_data)
    result = res.json()

    assert result["name"] == "Grace"
    assert result["city"] == "Springfield"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_nested_model_missing_nested_fields(function_type: str, session):
    """Missing fields in nested model should produce errors with correct nested loc paths."""
    json_data = {
        "name": "Grace",
        "email": "grace@example.com",
        "address": {"street": "123 Main St"},  # missing city and zip_code
    }
    res = json_post(
        f"/{function_type}/pydantic/nested",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"

    errors = result["detail"]
    error_locs = {tuple(e["loc"]) for e in errors}
    assert ("address", "city") in error_locs
    assert ("address", "zip_code") in error_locs

    for err in errors:
        assert err["type"] == "missing"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_nested_model_missing_entirely(function_type: str, session):
    """Missing the entire nested object should produce an error at the parent field."""
    json_data = {"name": "Grace", "email": "grace@example.com"}
    res = json_post(
        f"/{function_type}/pydantic/nested",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()

    errors = result["detail"]
    address_errors = [e for e in errors if e["loc"] == ["address"]]
    assert len(address_errors) == 1
    assert address_errors[0]["type"] == "missing"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_nested_model_wrong_type(function_type: str, session):
    """Passing a non-object for the nested model should return 422."""
    json_data = {
        "name": "Grace",
        "email": "grace@example.com",
        "address": "not an object",
    }
    res = json_post(
        f"/{function_type}/pydantic/nested",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    errors = result["detail"]
    address_errors = [e for e in errors if "address" in e["loc"]]
    assert len(address_errors) >= 1


# ===== Pydantic with PUT =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_put_valid(function_type: str, session):
    """Pydantic validation must work with PUT method."""
    json_data = {"name": "Hank", "email": "hank@example.com", "age": 40}
    res = requests.put(f"{BASE_URL}/{function_type}/pydantic/user", json=json_data)
    result = res.json()

    assert result["updated"] is True
    assert result["name"] == "Hank"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_put_invalid(function_type: str, session):
    """PUT with invalid body must also return 422 with proper error structure."""
    json_data = {"name": "Hank"}  # missing email and age
    res = requests.put(f"{BASE_URL}/{function_type}/pydantic/user", json=json_data)
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"
    error_fields = {tuple(e["loc"]) for e in result["detail"]}
    assert ("email",) in error_fields
    assert ("age",) in error_fields


# ===== Pydantic with PATCH =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_patch_valid(function_type: str, session):
    """Pydantic validation must work with PATCH method."""
    json_data = {"name": "Iris", "email": "iris@example.com", "age": 29}
    res = requests.patch(f"{BASE_URL}/{function_type}/pydantic/user", json=json_data)
    result = res.json()

    assert result["patched"] is True
    assert result["name"] == "Iris"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_patch_invalid(function_type: str, session):
    """PATCH with invalid body must also return 422."""
    json_data = {"name": "Iris"}  # missing email and age
    res = requests.patch(f"{BASE_URL}/{function_type}/pydantic/user", json=json_data)
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"
    error_fields = {tuple(e["loc"]) for e in result["detail"]}
    assert ("email",) in error_fields
    assert ("age",) in error_fields


# ===== Pydantic with DELETE =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_delete_valid(function_type: str, session):
    """Pydantic validation must work with DELETE method."""
    json_data = {"name": "Zara", "email": "zara@example.com", "age": 33}
    res = requests.delete(f"{BASE_URL}/{function_type}/pydantic/user", json=json_data)
    result = res.json()

    assert result["deleted"] is True
    assert result["name"] == "Zara"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_delete_invalid(function_type: str, session):
    """DELETE with invalid body must also return 422 with proper error structure."""
    json_data = {"name": "Zara"}  # missing email and age
    res = requests.delete(f"{BASE_URL}/{function_type}/pydantic/user", json=json_data)
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"
    error_fields = {tuple(e["loc"]) for e in result["detail"]}
    assert ("email",) in error_fields
    assert ("age",) in error_fields


# ===== Returning Pydantic models directly =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_return_model_directly(function_type: str, session):
    """Returning a Pydantic model from a handler should auto-serialize to JSON."""
    json_data = {"name": "Jack", "email": "jack@example.com", "age": 32}
    res = requests.post(f"{BASE_URL}/{function_type}/pydantic/return_model", json=json_data)

    assert res.status_code == 200
    assert "application/json" in res.headers.get("content-type", "")

    result = res.json()
    assert result["name"] == "Jack"
    assert result["email"] == "jack@example.com"
    assert result["age"] == 32
    assert result["active"] is True  # default field


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_return_model_preserves_all_fields(function_type: str, session):
    """Returned model should include every field, including those with defaults."""
    json_data = {"name": "Kate", "email": "kate@example.com", "age": 27, "active": False}
    res = requests.post(f"{BASE_URL}/{function_type}/pydantic/return_model", json=json_data)
    result = res.json()

    assert result["name"] == "Kate"
    assert result["email"] == "kate@example.com"
    assert result["age"] == 27
    assert result["active"] is False


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_return_model_validation_still_works(function_type: str, session):
    """Validation should still trigger 422 even when the route returns a model."""
    json_data = {"name": "Kate"}  # missing email and age
    res = requests.post(f"{BASE_URL}/{function_type}/pydantic/return_model", json=json_data)
    assert res.status_code == 422
    result = res.json()
    assert result["error"] == "Validation Error"


# ===== Returning lists of Pydantic models =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_return_list_of_models(function_type: str, session):
    """Returning a list of Pydantic models should auto-serialize to a JSON array."""
    json_data = {"name": "Leo", "email": "leo@example.com", "age": 45}
    res = requests.post(f"{BASE_URL}/{function_type}/pydantic/return_list", json=json_data)

    assert res.status_code == 200
    assert "application/json" in res.headers.get("content-type", "")

    result = res.json()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "Leo"
    assert result[1]["name"] == "Leo"
    assert result[0]["active"] is True
