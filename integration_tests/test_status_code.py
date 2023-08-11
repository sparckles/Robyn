import pytest
from integration_tests.helpers.http_methods_helpers import get


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
