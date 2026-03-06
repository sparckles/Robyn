import pytest

from integration_tests.helpers.http_methods_helpers import json_post

try:
    import pydantic

    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False

pytestmark = pytest.mark.skipif(not _HAS_PYDANTIC, reason="pydantic not installed")


# ===== Valid Pydantic Body =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_valid_user(function_type: str, session):
    """Valid JSON body should be validated and returned as model fields."""
    json_data = {"name": "Alice", "email": "alice@example.com", "age": 30, "active": True}
    res = json_post(f"/{function_type}/pydantic/user", json_data=json_data)
    result = res.json()

    assert result["name"] == "Alice"
    assert result["email"] == "alice@example.com"
    assert result["age"] == 30
    assert result["active"] is True


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_default_field(function_type: str, session):
    """Fields with defaults should use the default when not provided."""
    json_data = {"name": "Bob", "email": "bob@example.com", "age": 25}
    res = json_post(f"/{function_type}/pydantic/user", json_data=json_data)
    result = res.json()

    assert result["name"] == "Bob"
    assert result["active"] is True  # default value


# ===== Invalid Pydantic Body =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_missing_required_field(function_type: str, session):
    """Missing a required field should return 422."""
    json_data = {"name": "Charlie", "email": "charlie@example.com"}  # missing 'age'
    res = json_post(
        f"/{function_type}/pydantic/user",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    assert "detail" in result


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_wrong_type(function_type: str, session):
    """Wrong type for a field should return 422."""
    json_data = {"name": "Diana", "email": "diana@example.com", "age": "not_a_number"}
    res = json_post(
        f"/{function_type}/pydantic/user",
        json_data=json_data,
        expected_status_code=422,
        should_check_response=False,
    )
    assert res.status_code == 422
    result = res.json()
    assert "detail" in result


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_invalid_json(function_type: str, session):
    """Completely invalid JSON should return 422."""
    import requests

    endpoint = f"/{function_type}/pydantic/user".lstrip("/")
    res = requests.post(
        f"http://127.0.0.1:8080/{endpoint}",
        data="not json at all {{{",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 422


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_extra_fields_ignored(function_type: str, session):
    """Extra fields not in the model should be ignored (default pydantic v2 behavior)."""
    json_data = {"name": "Eve", "email": "eve@example.com", "age": 28, "extra_field": "should_be_ignored"}
    res = json_post(f"/{function_type}/pydantic/user", json_data=json_data)
    result = res.json()

    assert result["name"] == "Eve"
    assert result["age"] == 28
    assert "extra_field" not in result


# ===== Pydantic + Request object =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_with_request(function_type: str, session):
    """Handler can accept both Request and a Pydantic model."""
    json_data = {"name": "Frank", "email": "frank@example.com", "age": 35}
    res = json_post(f"/{function_type}/pydantic/user_with_request", json_data=json_data)
    result = res.json()

    assert result["method"] == "POST"
    assert result["name"] == "Frank"
    assert result["email"] == "frank@example.com"


# ===== Nested Pydantic Models =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_nested_model(function_type: str, session):
    """Nested Pydantic models should be validated recursively."""
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
def test_pydantic_nested_model_invalid(function_type: str, session):
    """Invalid nested model should return 422."""
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


# ===== Pydantic with PUT =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_put(function_type: str, session):
    """Pydantic models should work with PUT method too."""
    import requests

    json_data = {"name": "Hank", "email": "hank@example.com", "age": 40}
    res = requests.put(f"http://127.0.0.1:8080/{function_type}/pydantic/user", json=json_data)
    result = res.json()

    assert result["updated"] is True
    assert result["name"] == "Hank"


# ===== Empty body =====


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_pydantic_empty_body(function_type: str, session):
    """Empty body should return 422."""
    import requests

    endpoint = f"/{function_type}/pydantic/user".lstrip("/")
    res = requests.post(f"http://127.0.0.1:8080/{endpoint}", data="", headers={"Content-Type": "application/json"})
    assert res.status_code == 422
