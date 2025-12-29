from robyn.openapi import OpenAPI, OpenAPIInfo


def test_openapi_nested_path_parsing():
    """
    Test for Issue #1270: Ensures nested path parameters
    like /users/:id/posts/:post_id are parsed correctly.
    """
    # Initialize OpenAPI with default info
    openapi = OpenAPI(info=OpenAPIInfo())

    # A dummy handler for the test
    def mock_handler():
        pass

    # Add the problematic nested route
    openapi.add_openapi_path_obj(
        route_type="get", endpoint="/users/:id/posts/:post_id", openapi_name="get_user_posts", openapi_tags=["testing"], handler=mock_handler
    )

    generated_spec = openapi.get_openapi_config()
    paths = generated_spec["paths"]

    # 1. Verify the path key uses OpenAPI curly brace syntax
    expected_path = "/users/{id}/posts/{post_id}"
    assert expected_path in paths, f"Expected {expected_path} but found {list(paths.keys())}"

    # 2. Verify parameters are extracted individually
    params = paths[expected_path]["get"]["parameters"]
    param_names = [p["name"] for p in params]

    assert "id" in param_names
    assert "post_id" in param_names

    # Specifically ensure the slash wasn't swallowed into the parameter name
    assert "id/posts" not in param_names
