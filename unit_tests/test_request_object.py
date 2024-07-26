import pytest
from robyn.openapi_middleware import OpenAPIMiddleware, OpenAPIInfo
from robyn.robyn import Headers, QueryParams, Request, Url

# Fixtures to set up the necessary objects
@pytest.fixture
def app():
    return type('TestApp', (), {})()  # Mock app object

@pytest.fixture
def middleware(app):
    return OpenAPIMiddleware(app)

def test_update_info(middleware):
    # Initial assertions
    assert middleware.info.title == "Robyn API"
    assert middleware.info.version == "1.0.0"
    assert middleware.info.description is None

    # Update the info
    middleware.update_info(
        title="My Custom API",
        version="2.0.0",
        description="This is a custom API",
        termsOfService="http://example.com/terms/",
        contact_name="API Support",
        contact_url="http://www.example.com/support",
        contact_email="support@example.com",
        license_name="Apache 2.0",
        license_url="http://www.apache.org/licenses/LICENSE-2.0.html",
        servers=[{"url": "https://api.example.com", "description": "Production server"}],
        externalDocs={"description": "Find more info here", "url": "http://example.com/docs"},
        component_schemas={
            "Error": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "code": {"type": "integer"}
                }
            }
        }
    )

    # Assertions after update
    assert middleware.info.title == "My Custom API"
    assert middleware.info.version == "2.0.0"
    assert middleware.info.description == "This is a custom API"
    assert middleware.info.termsOfService == "http://example.com/terms/"
    assert middleware.info.contact.name == "API Support"
    assert middleware.info.contact.url == "http://www.example.com/support"
    assert middleware.info.contact.email == "support@example.com"
    assert middleware.info.license.name == "Apache 2.0"
    assert middleware.info.license.url == "http://www.apache.org/licenses/LICENSE-2.0.html"
    assert len(middleware.info.servers) == 1
    assert middleware.info.servers[0].url == "https://api.example.com"
    assert middleware.info.servers[0].description == "Production server"
    assert middleware.info.externalDocs.description == "Find more info here"
    assert middleware.info.externalDocs.url == "http://example.com/docs"
    assert "Error" in middleware.info.components.schemas

def test_request_object():
    url = Url(
        scheme="https",
        host="localhost",
        path="/user",
    )
    request = Request(
        query_params=QueryParams(),
        headers=Headers({"Content-Type": "application/json"}),
        path_params={},
        body="",
        method="GET",
        url=url,
        ip_addr=None,
        identity=None,
        form_data={},
        files={},
    )

    assert request.url.scheme == "https"
    assert request.url.host == "localhost"
    assert request.headers.get("Content-Type") == "application/json"
    assert request.method == "GET"
