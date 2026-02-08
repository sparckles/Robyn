import pytest
import requests

from integration_tests.helpers.http_methods_helpers import BASE_URL, get


@pytest.mark.benchmark
def test_404_status_code(session):
    get("/404", expected_status_code=404)


@pytest.mark.benchmark
def test_404_not_found(session):
    r = get("/real/404", expected_status_code=404)
    assert r.text == "Not found"


@pytest.mark.benchmark
def test_202_status_code(session):
    get("/202", expected_status_code=202)


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_sync_500_internal_server_error(function_type: str, session):
    get(f"/{function_type}/raise", expected_status_code=500)


# ===== Content-Type on error responses =====


@pytest.mark.benchmark
def test_404_not_found_content_type(session):
    """A request to a non-existent route should return Content-Type: text/plain"""
    r = get("/real/404", expected_status_code=404)
    assert r.text == "Not found"
    content_type = r.headers.get("Content-Type", "")
    assert "text/plain" in content_type


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_500_error_content_type(function_type: str, session):
    """An unhandled exception should return Content-Type: text/plain"""
    r = get(f"/{function_type}/raise", expected_status_code=500)
    content_type = r.headers.get("Content-Type", "")
    assert "text/plain" in content_type


@pytest.mark.benchmark
def test_405_method_not_allowed_content_type(session):
    """An unsupported HTTP method should return 405 with Content-Type: text/plain"""
    response = requests.request("NONSTANDARD", f"{BASE_URL}/")
    assert response.status_code == 405
    content_type = response.headers.get("Content-Type", "")
    assert "text/plain" in content_type
