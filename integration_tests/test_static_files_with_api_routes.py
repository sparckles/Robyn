"""
Test for issue #1251: Verify that API routes work correctly
when static files are served from the same base path.

This test ensures that non-GET/HEAD HTTP methods properly fall through
to API handlers when a static file service is mounted at the same route.
"""

import pytest

from integration_tests.helpers.http_methods_helpers import generic_http_helper, get, post

# Notes:
# 1. The /static route serves the integration_tests having files & directories.


@pytest.mark.benchmark
def test_post_api_route_with_root_static_files(session):
    """Test that POST requests reach API handlers (issue #1251).
    This ensures that non-GET/HEAD methods are not blocked by static file serving.
    """
    response = post("/static/build")
    assert response.status_code == 200
    assert response.text == f"{response.request.method}:{response.request.path_url} works"


@pytest.mark.benchmark
def test_static_file_still_served_correctly(session):
    """Verify that actual static files are still served correctly."""
    response = get("/static/build/index.html", should_check_response=False)
    assert response.status_code == 200
    # Should serve the index.html file
    assert "html" in response.text.lower()


def test_options_route_under_static_mount_reaches_router(session):
    """#1130: an OPTIONS route under a static mount must reach the router rather
    than being swallowed by the file service."""
    response = generic_http_helper("options", "/test_dir/preflight", should_check_response=False)
    assert response.status_code == 200
    assert response.text == "options-under-static"
