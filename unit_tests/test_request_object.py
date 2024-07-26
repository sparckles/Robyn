import unittest
from robyn.openapi_middleware import OpenAPIMiddleware
from robyn.robyn import Headers, QueryParams, Request, Url


class TestOpenAPIMiddleware(unittest.TestCase):
    def setUp(self):
        self.app = type("TestApp", (), {})()  # Mock app object
        self.middleware = OpenAPIMiddleware(self.app)

    def test_update_info(self):
        # Initial assertions
        self.assertEqual(self.middleware.info.title, "Robyn API")
        self.assertEqual(self.middleware.info.version, "1.0.0")
        self.assertIsNone(self.middleware.info.description)

        # Update the info
        self.middleware.update_info(
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
            component_schemas={"Error": {"type": "object", "properties": {"message": {"type": "string"}, "code": {"type": "integer"}}}},
        )

        # Assertions after update
        self.assertEqual(self.middleware.info.title, "My Custom API")
        self.assertEqual(self.middleware.info.version, "2.0.0")
        self.assertEqual(self.middleware.info.description, "This is a custom API")
        self.assertEqual(self.middleware.info.termsOfService, "http://example.com/terms/")
        self.assertEqual(self.middleware.info.contact.name, "API Support")
        self.assertEqual(self.middleware.info.contact.url, "http://www.example.com/support")
        self.assertEqual(self.middleware.info.contact.email, "support@example.com")
        self.assertEqual(self.middleware.info.license.name, "Apache 2.0")
        self.assertEqual(self.middleware.info.license.url, "http://www.apache.org/licenses/LICENSE-2.0.html")
        self.assertEqual(len(self.middleware.info.servers), 1)
        self.assertEqual(self.middleware.info.servers[0].url, "https://api.example.com")
        self.assertEqual(self.middleware.info.servers[0].description, "Production server")
        self.assertEqual(self.middleware.info.externalDocs.description, "Find more info here")
        self.assertEqual(self.middleware.info.externalDocs.url, "http://example.com/docs")
        self.assertIn("Error", self.middleware.info.components.schemas)


class TestRequestObject(unittest.TestCase):
    def test_request_object(self):
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

        self.assertEqual(request.url.scheme, "https")
        self.assertEqual(request.url.host, "localhost")
        print(request.headers.get("Content-Type"))
        self.assertEqual(request.headers.get("Content-Type"), "application/json")
        self.assertEqual(request.method, "GET")


if __name__ == "__main__":
    unittest.main()
