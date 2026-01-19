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

    # 1. Test Standard Nested Route
    openapi.add_openapi_path_obj(
        route_type="get", endpoint="/users/:id/posts/:post_id", openapi_name="get_user_posts", openapi_tags=["testing"], handler=mock_handler
    )

    # 2. Test Parameters with Underscores
    openapi.add_openapi_path_obj(
        route_type="get", endpoint="/orgs/:org_id/members/:user_id", openapi_name="get_org_member", openapi_tags=["testing"], handler=mock_handler
    )

    # 3. Test Triple Nested Parameters
    openapi.add_openapi_path_obj(route_type="get", endpoint="/a/:p1/b/:p2/c/:p3", openapi_name="triple_nested", openapi_tags=["testing"], handler=mock_handler)

    # 4. Test Route Without Parameters (Static)
    openapi.add_openapi_path_obj(route_type="get", endpoint="/health", openapi_name="health_check", openapi_tags=["testing"], handler=mock_handler)

    generated_spec = openapi.get_openapi_config()
    paths = generated_spec["paths"]

    # Assertions for Case 1: Standard Nested
    expected_path_1 = "/users/{id}/posts/{post_id}"
    assert expected_path_1 in paths
    params_1 = [p["name"] for p in paths[expected_path_1]["get"]["parameters"]]
    assert "id" in params_1
    assert "post_id" in params_1
    assert "id/posts" not in params_1

    # Assertions for Case 2: Underscores
    expected_path_2 = "/orgs/{org_id}/members/{user_id}"
    assert expected_path_2 in paths
    params_2 = [p["name"] for p in paths[expected_path_2]["get"]["parameters"]]
    assert "org_id" in params_2
    assert "user_id" in params_2

    # Assertions for Case 3: Triple Nested
    expected_path_3 = "/a/{p1}/b/{p2}/c/{p3}"
    assert expected_path_3 in paths
    params_3 = [p["name"] for p in paths[expected_path_3]["get"]["parameters"]]
    assert len(params_3) == 3

    # Assertions for Case 4: Static Route
    assert "/health" in paths
    assert len(paths["/health"]["get"]["parameters"]) == 0
