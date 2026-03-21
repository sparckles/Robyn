from robyn.openapi import Components, OpenAPI, OpenAPIInfo


BEARER_SCHEME = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
API_KEY_SCHEME = {"type": "apiKey", "in": "header", "name": "X-API-Key"}


def _make_openapi(**kwargs) -> OpenAPI:
    return OpenAPI(info=OpenAPIInfo(**kwargs))


def test_security_schemes_via_constructor():
    """securitySchemes passed through Components should appear in the generated spec."""
    openapi = _make_openapi(
        components=Components(securitySchemes={"BearerAuth": BEARER_SCHEME}),
        security=[{"BearerAuth": []}],
    )
    spec = openapi.get_openapi_config()

    assert spec["components"]["securitySchemes"]["BearerAuth"] == BEARER_SCHEME
    assert spec["security"] == [{"BearerAuth": []}]


def test_no_security_by_default():
    """When no security schemes are configured, 'security' key should not appear."""
    openapi = _make_openapi()
    spec = openapi.get_openapi_config()

    assert spec["components"]["securitySchemes"] == {}
    assert "security" not in spec


def test_add_security_scheme_applies_globally():
    """add_security_scheme with apply_globally=True should populate both
    components.securitySchemes and the top-level security array."""
    openapi = _make_openapi()
    openapi.add_security_scheme("BearerAuth", BEARER_SCHEME)

    spec = openapi.get_openapi_config()
    assert spec["components"]["securitySchemes"]["BearerAuth"] == BEARER_SCHEME
    assert {"BearerAuth": []} in spec["security"]


def test_add_security_scheme_without_global():
    """add_security_scheme with apply_globally=False should only add to
    components.securitySchemes, not the top-level security."""
    openapi = _make_openapi()
    openapi.add_security_scheme("ApiKey", API_KEY_SCHEME, apply_globally=False)

    spec = openapi.get_openapi_config()
    assert spec["components"]["securitySchemes"]["ApiKey"] == API_KEY_SCHEME
    assert "security" not in spec


def test_multiple_security_schemes():
    """Multiple schemes can be added and all appear in the spec."""
    openapi = _make_openapi()
    openapi.add_security_scheme("BearerAuth", BEARER_SCHEME)
    openapi.add_security_scheme("ApiKey", API_KEY_SCHEME)

    spec = openapi.get_openapi_config()
    assert "BearerAuth" in spec["components"]["securitySchemes"]
    assert "ApiKey" in spec["components"]["securitySchemes"]
    assert {"BearerAuth": []} in spec["security"]
    assert {"ApiKey": []} in spec["security"]


def test_auth_required_route_gets_security():
    """Routes with auth_required=True should have per-operation security
    when security schemes are configured."""
    openapi = _make_openapi(
        components=Components(securitySchemes={"BearerAuth": BEARER_SCHEME}),
    )

    def handler():
        pass

    openapi.add_openapi_path_obj("get", "/protected", "protected", ["test"], handler, auth_required=True)
    spec = openapi.get_openapi_config()

    operation = spec["paths"]["/protected"]["get"]
    assert "security" in operation
    assert {"BearerAuth": []} in operation["security"]


def test_auth_required_without_schemes_no_security():
    """Routes with auth_required=True but no configured security schemes
    should not have a security field in the operation."""
    openapi = _make_openapi()

    def handler():
        pass

    openapi.add_openapi_path_obj("get", "/protected", "protected", ["test"], handler, auth_required=True)
    spec = openapi.get_openapi_config()

    operation = spec["paths"]["/protected"]["get"]
    assert "security" not in operation


def test_public_route_no_security():
    """Routes without auth_required should not have per-operation security
    even when security schemes are configured."""
    openapi = _make_openapi(
        components=Components(securitySchemes={"BearerAuth": BEARER_SCHEME}),
    )

    def handler():
        pass

    openapi.add_openapi_path_obj("get", "/public", "public", ["test"], handler, auth_required=False)
    spec = openapi.get_openapi_config()

    operation = spec["paths"]["/public"]["get"]
    assert "security" not in operation


def test_add_security_scheme_ignored_when_overridden():
    """add_security_scheme should be a no-op when an openapi file override is active."""
    openapi = _make_openapi()
    openapi.openapi_spec = {"openapi": "3.1.0", "paths": {}, "components": {}}
    openapi.openapi_file_override = True

    openapi.add_security_scheme("BearerAuth", BEARER_SCHEME)

    assert "securitySchemes" not in openapi.openapi_spec.get("components", {})
