import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
def test_local_dependency_injection(benchmark):
    r = get("/local_dependency_injection")
    assert r.status_code == 200
    assert r.text == "route_dependency"


@pytest.mark.benchmark
def test_global_dependency_injection(benchmark):
    r = get("/global_dependency_injection")
    assert r.status_code == 200
    assert r.text == "global_dependency"
