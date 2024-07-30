import pytest

from robyn import OpenAPI
from robyn.responses import FileResponse


@pytest.fixture
def openapi_instance():
    return OpenAPI()


@pytest.fixture
def subrouter_openapi_instance():
    return OpenAPI()


def test_openapi_initialization(openapi_instance):
    spec = openapi_instance.openapi_spec
    assert spec["openapi"] == "3.0.0"
    assert spec["info"]["title"] == "Robyn API"
    assert spec["info"]["version"] == "1.0.0"
    assert "paths" in spec
    assert "components" in spec
    assert "servers" in spec
    assert "externalDocs" in spec


def test_docs_handler(openapi_instance):
    html_response = openapi_instance.docs_handler()
    assert isinstance(html_response, FileResponse)


def test_json_handler(openapi_instance):
    json_response = openapi_instance.json_handler()
    assert isinstance(json_response, str)
    assert "openapi" in json_response
    assert "info" in json_response
    assert "paths" in json_response
    assert "components" in json_response
    assert "servers" in json_response
    assert "externalDocs" in json_response


def test_add_openapi_path(openapi_instance):
    route_type = "get"
    endpoint = "/users"
    openapi_summary = "Get users"
    openapi_tags = ["users"]

    openapi_instance.add_openapi_path_obj(route_type, endpoint, openapi_summary, openapi_tags)

    assert endpoint in openapi_instance.openapi_spec["paths"]
    assert route_type in openapi_instance.openapi_spec["paths"][endpoint]
    assert openapi_summary == openapi_instance.openapi_spec["paths"][endpoint][route_type]["summary"]
    assert openapi_tags == openapi_instance.openapi_spec["paths"][endpoint][route_type]["tags"]


def test_add_subrouter_paths(openapi_instance, subrouter_openapi_instance):
    route_type = "post"
    endpoint = "/users/appointment"
    openapi_summary = "Get Appointment"
    openapi_tags = ["appointment"]

    subrouter_openapi_instance.add_openapi_path_obj(route_type, endpoint, openapi_summary, openapi_tags)

    openapi_instance.add_subrouter_paths(subrouter_openapi_instance)

    assert endpoint in openapi_instance.openapi_spec["paths"]
    assert route_type in openapi_instance.openapi_spec["paths"][endpoint]
    assert openapi_summary == openapi_instance.openapi_spec["paths"][endpoint][route_type]["summary"]
    assert openapi_tags == openapi_instance.openapi_spec["paths"][endpoint][route_type]["tags"]
