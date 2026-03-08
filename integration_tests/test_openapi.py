import pytest

from integration_tests.helpers.http_methods_helpers import get
from robyn import Robyn


@pytest.mark.benchmark
def test_custom_openapi_spec():
    app = Robyn(__file__, openapi_file_path="openapi_config.json")

    openapi_spec = app.openapi.openapi_spec

    assert isinstance(openapi_spec, dict)

    assert "openapi" in openapi_spec
    assert "info" in openapi_spec
    assert "paths" in openapi_spec
    assert "components" in openapi_spec
    assert "servers" in openapi_spec
    assert "externalDocs" in openapi_spec

    assert openapi_spec["info"]["title"] == "Robyn Test API"
    assert openapi_spec["info"]["version"] == "1.0.0"


@pytest.mark.benchmark
def test_docs_handler():
    # should_check_response = False because check_response raises a
    # failure if the global headers are not present in the response
    # provided we are excluding headers for /docs and /openapi.json
    html_response = get("/docs", should_check_response=False)
    assert html_response.status_code == 200


@pytest.mark.benchmark
def test_json_handler():
    openapi_response = get("/openapi.json", should_check_response=False)

    assert openapi_response.status_code == 200

    openapi_spec = openapi_response.json()

    assert isinstance(openapi_spec, dict)
    assert "openapi" in openapi_spec
    assert "info" in openapi_spec
    assert "paths" in openapi_spec
    assert "components" in openapi_spec
    assert "servers" in openapi_spec
    assert "externalDocs" in openapi_spec


@pytest.mark.benchmark
def test_add_openapi_path():
    openapi_response = get("/openapi.json", should_check_response=False)

    assert openapi_response.status_code == 200

    openapi_spec = openapi_response.json()

    assert isinstance(openapi_spec, dict)

    route_type = "get"
    endpoint = "/openapi_test"
    openapi_description = "Get openapi"
    openapi_tags = ["test tag"]

    assert endpoint in openapi_spec["paths"]
    assert route_type in openapi_spec["paths"][endpoint]
    assert openapi_description == openapi_spec["paths"][endpoint][route_type]["description"]
    assert openapi_tags == openapi_spec["paths"][endpoint][route_type]["tags"]


@pytest.mark.benchmark
def test_add_subrouter_paths():
    openapi_response = get("/openapi.json", should_check_response=False)

    assert openapi_response.status_code == 200

    openapi_spec = openapi_response.json()

    assert isinstance(openapi_spec, dict)

    route_type = "post"
    endpoint = "/sub_router/openapi_test"
    openapi_description = "Get subrouter openapi"
    openapi_tags = ["test subrouter tag"]

    assert endpoint in openapi_spec["paths"]
    assert route_type in openapi_spec["paths"][endpoint]
    assert openapi_description == openapi_spec["paths"][endpoint][route_type]["description"]
    assert openapi_tags == openapi_spec["paths"][endpoint][route_type]["tags"]


@pytest.mark.benchmark
def test_openapi_request_body():
    openapi_response = get("/openapi.json", should_check_response=False)

    assert openapi_response.status_code == 200

    openapi_spec = openapi_response.json()

    assert isinstance(openapi_spec, dict)

    route_type = "post"
    endpoint = "/openapi_request_body"

    assert endpoint in openapi_spec["paths"]
    assert route_type in openapi_spec["paths"][endpoint]
    assert "requestBody" in openapi_spec["paths"][endpoint][route_type]
    assert "content" in openapi_spec["paths"][endpoint][route_type]["requestBody"]
    assert "application/json" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]
    assert "schema" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]
    assert "properties" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]

    assert "name" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]
    assert "description" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]
    assert "price" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]
    assert "tax" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]

    assert "string" == openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["description"]["type"]
    assert "number" == openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["price"]["type"]
    assert "number" == openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["tax"]["type"]

    assert "object" == openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"]["type"]

    assert "first" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"]["properties"]
    assert "second" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"]["properties"]
    assert "initial" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"]["properties"]

    assert (
        "object"
        in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"]["properties"]["initial"][
            "type"
        ]
    )

    assert (
        "is_present"
        in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"]["properties"]["initial"][
            "properties"
        ]
    )
    assert (
        "letter"
        in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"]["properties"]["initial"][
            "properties"
        ]
    )

    assert {"type": "string"} in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"][
        "properties"
    ]["initial"]["properties"]["letter"]["anyOf"]
    assert {"type": "null"} in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]["name"][
        "properties"
    ]["initial"]["properties"]["letter"]["anyOf"]


@pytest.mark.benchmark
def test_openapi_response_body():
    openapi_response = get("/openapi.json", should_check_response=False)

    assert openapi_response.status_code == 200

    openapi_spec = openapi_response.json()

    assert isinstance(openapi_spec, dict)

    route_type = "post"
    endpoint = "/openapi_request_body"

    assert endpoint in openapi_spec["paths"]
    assert route_type in openapi_spec["paths"][endpoint]
    assert "responses" in openapi_spec["paths"][endpoint][route_type]
    assert "200" in openapi_spec["paths"][endpoint][route_type]["responses"]

    assert openapi_spec["paths"][endpoint][route_type]["responses"]["200"]["description"] == "Successful Response"

    assert "content" in openapi_spec["paths"][endpoint][route_type]["responses"]["200"]

    assert "application/json" in openapi_spec["paths"][endpoint][route_type]["responses"]["200"]["content"]
    assert "schema" in openapi_spec["paths"][endpoint][route_type]["responses"]["200"]["content"]["application/json"]
    assert "properties" in openapi_spec["paths"][endpoint][route_type]["responses"]["200"]["content"]["application/json"]["schema"]

    assert "success" in openapi_spec["paths"][endpoint][route_type]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]
    assert "items_changed" in openapi_spec["paths"][endpoint][route_type]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]

    assert (
        "boolean" == openapi_spec["paths"][endpoint][route_type]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["success"]["type"]
    )

    assert (
        "integer"
        == openapi_spec["paths"][endpoint][route_type]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["items_changed"]["type"]
    )


@pytest.mark.benchmark
def test_openapi_query_params():
    openapi_response = get("/openapi.json", should_check_response=False)

    assert openapi_response.status_code == 200

    openapi_spec = openapi_response.json()

    assert isinstance(openapi_spec, dict)

    route_type = "post"
    endpoint = "/openapi_request_body"

    assert endpoint in openapi_spec["paths"]
    assert route_type in openapi_spec["paths"][endpoint]
    assert "parameters" in openapi_spec["paths"][endpoint][route_type]

    assert "required" == openapi_spec["paths"][endpoint][route_type]["parameters"][0]["name"]
    assert "query" == openapi_spec["paths"][endpoint][route_type]["parameters"][0]["in"]
    assert {"type": "boolean"} == openapi_spec["paths"][endpoint][route_type]["parameters"][0]["schema"]


@pytest.mark.benchmark
def test_openapi_json_body_typed():
    """Test that a typed JsonBody subclass generates a proper requestBody schema in OpenAPI docs."""
    openapi_response = get("/openapi.json", should_check_response=False)

    assert openapi_response.status_code == 200

    openapi_spec = openapi_response.json()

    assert isinstance(openapi_spec, dict)

    route_type = "post"
    endpoint = "/openapi_json_body"

    assert endpoint in openapi_spec["paths"]
    assert route_type in openapi_spec["paths"][endpoint]
    assert "requestBody" in openapi_spec["paths"][endpoint][route_type]
    assert "content" in openapi_spec["paths"][endpoint][route_type]["requestBody"]
    assert "application/json" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]
    assert "schema" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]
    assert "properties" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]

    properties = openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]["application/json"]["schema"]["properties"]
    assert "fahrenheit" in properties
    assert "number" == properties["fahrenheit"]["type"]


@pytest.mark.benchmark
def test_openapi_json_body_bare():
    """Test that a bare JsonBody generates a requestBody with empty properties in OpenAPI docs."""
    openapi_response = get("/openapi.json", should_check_response=False)

    assert openapi_response.status_code == 200

    openapi_spec = openapi_response.json()

    assert isinstance(openapi_spec, dict)

    route_type = "post"
    # bare JsonBody routes should still have requestBody in the spec
    endpoint = "/sync/json_body/bare"

    assert endpoint in openapi_spec["paths"]
    assert route_type in openapi_spec["paths"][endpoint]
    assert "requestBody" in openapi_spec["paths"][endpoint][route_type]
    assert "content" in openapi_spec["paths"][endpoint][route_type]["requestBody"]
    assert "application/json" in openapi_spec["paths"][endpoint][route_type]["requestBody"]["content"]


try:
    import pydantic  # noqa: F401

    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False


@pytest.mark.benchmark
@pytest.mark.skipif(not _HAS_PYDANTIC, reason="pydantic not installed")
def test_openapi_pydantic_request_body():
    """Pydantic model on a regular route should produce a full JSON Schema in
    requestBody — no dedicated OpenAPI route needed."""
    openapi_response = get("/openapi.json", should_check_response=False)
    assert openapi_response.status_code == 200
    openapi_spec = openapi_response.json()

    endpoint = "/sync/pydantic/user"
    route = openapi_spec["paths"][endpoint]["post"]

    assert route["tags"] == ["pydantic"]
    assert route["description"] == "Create a user with Pydantic validation"

    assert "requestBody" in route
    schema = route["requestBody"]["content"]["application/json"]["schema"]

    assert schema["type"] == "object"
    assert schema["title"] == "UserCreate"

    props = schema["properties"]
    assert props["name"]["type"] == "string"
    assert props["name"]["title"] == "Name"
    assert props["email"]["type"] == "string"
    assert props["email"]["title"] == "Email"
    assert props["age"]["type"] == "integer"
    assert props["age"]["title"] == "Age"
    assert props["active"]["type"] == "boolean"
    assert props["active"]["title"] == "Active"
    assert props["active"]["default"] is True

    assert set(schema["required"]) == {"name", "email", "age"}
    assert "active" not in schema["required"]

    assert "responses" in route
    assert "200" in route["responses"]
    assert "application/json" in route["responses"]["200"]["content"]


@pytest.mark.benchmark
@pytest.mark.skipif(not _HAS_PYDANTIC, reason="pydantic not installed")
def test_openapi_pydantic_nested_model():
    """Nested Pydantic models on a regular route should use $ref and populate
    components/schemas — no dedicated OpenAPI route needed."""
    openapi_response = get("/openapi.json", should_check_response=False)
    assert openapi_response.status_code == 200
    openapi_spec = openapi_response.json()

    endpoint = "/sync/pydantic/nested"
    route = openapi_spec["paths"][endpoint]["post"]

    assert route["tags"] == ["pydantic"]
    assert route["description"] == "Create a user with nested address"

    schema = route["requestBody"]["content"]["application/json"]["schema"]
    assert schema["type"] == "object"
    assert schema["title"] == "UserWithAddress"

    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["email"]["type"] == "string"
    assert schema["properties"]["address"]["$ref"] == "#/components/schemas/Address"

    assert set(schema["required"]) == {"name", "email", "address"}

    assert "Address" in openapi_spec["components"]["schemas"]
    address_schema = openapi_spec["components"]["schemas"]["Address"]
    assert address_schema["type"] == "object"
    assert address_schema["title"] == "Address"

    assert address_schema["properties"]["street"]["type"] == "string"
    assert address_schema["properties"]["street"]["title"] == "Street"
    assert address_schema["properties"]["city"]["type"] == "string"
    assert address_schema["properties"]["city"]["title"] == "City"
    assert address_schema["properties"]["zip_code"]["type"] == "string"
    assert address_schema["properties"]["zip_code"]["title"] == "Zip Code"

    assert set(address_schema["required"]) == {"street", "city", "zip_code"}

    assert "responses" in route
    assert "200" in route["responses"]
    assert "application/json" in route["responses"]["200"]["content"]


@pytest.mark.benchmark
@pytest.mark.skipif(not _HAS_PYDANTIC, reason="pydantic not installed")
def test_openapi_pydantic_return_type():
    """When a route has a Pydantic model as return type annotation, the response
    schema should reflect the full Pydantic model schema, not just 'object'."""
    openapi_response = get("/openapi.json", should_check_response=False)
    assert openapi_response.status_code == 200
    openapi_spec = openapi_response.json()

    endpoint = "/sync/pydantic/return_model"
    route = openapi_spec["paths"][endpoint]["post"]

    assert route["tags"] == ["pydantic"]
    assert route["description"] == "Return the validated Pydantic model directly"

    response_schema = route["responses"]["200"]["content"]["application/json"]["schema"]
    assert response_schema["type"] == "object"
    assert response_schema["title"] == "UserCreate"
    assert "properties" in response_schema
    assert response_schema["properties"]["name"]["type"] == "string"
    assert response_schema["properties"]["age"]["type"] == "integer"
    assert set(response_schema["required"]) == {"name", "email", "age"}
