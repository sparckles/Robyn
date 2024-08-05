import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
def test_docs_handler():
    html_response = get("/docs")
    assert html_response.status_code == 200


@pytest.mark.benchmark
def test_json_handler():
    json_response = get("/openapi.json").json()
    assert isinstance(json_response, dict)
    assert "openapi" in json_response
    assert "info" in json_response
    assert "paths" in json_response
    assert "components" in json_response
    assert "servers" in json_response
    assert "externalDocs" in json_response


@pytest.mark.benchmark
def test_add_openapi_path():
    json_response = get("/openapi.json").json()

    route_type = "get"
    endpoint = "/openapi_test"
    openapi_summary = "Get openapi"
    openapi_tags = ["test tag"]

    assert endpoint in json_response["paths"]
    assert route_type in json_response["paths"][endpoint]
    assert openapi_summary == json_response["paths"][endpoint][route_type]["summary"]
    assert openapi_tags == json_response["paths"][endpoint][route_type]["tags"]


@pytest.mark.benchmark
def test_add_subrouter_paths():
    json_response = get("/openapi.json").json()

    route_type = "post"
    endpoint = "/sub_router/openapi_test"
    openapi_summary = "Get subrouter openapi"
    # openapi_tags = ["test subrouter tag"]

    assert endpoint in json_response["paths"]
    assert route_type in json_response["paths"][endpoint]
    assert openapi_summary == json_response["paths"][endpoint][route_type]["summary"]
    # assert openapi_tags == openapi_instance.openapi_spec["paths"][endpoint][route_type]["tags"]
