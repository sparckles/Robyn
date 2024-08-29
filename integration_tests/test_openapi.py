import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
def test_docs_handler():
    html_response = get("/docs")
    assert html_response.status_code == 200


@pytest.mark.benchmark
def test_json_handler():
    openapi_spec = get("/openapi.json").json()

    assert isinstance(openapi_spec, dict)
    assert "openapi" in openapi_spec
    assert "info" in openapi_spec
    assert "paths" in openapi_spec
    assert "components" in openapi_spec
    assert "servers" in openapi_spec
    assert "externalDocs" in openapi_spec


@pytest.mark.benchmark
def test_add_openapi_path():
    openapi_spec = get("/openapi.json").json()

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
    openapi_spec = get("/openapi.json").json()

    assert isinstance(openapi_spec, dict)

    route_type = "post"
    endpoint = "/sub_router/openapi_test"
    openapi_description = "Get subrouter openapi"
    openapi_tags = ["test subrouter tag"]

    assert endpoint in openapi_spec["paths"]
    assert route_type in openapi_spec["paths"][endpoint]
    assert openapi_description == openapi_spec["paths"][endpoint][route_type]["description"]
    assert openapi_tags == openapi_spec["paths"][endpoint][route_type]["tags"]
