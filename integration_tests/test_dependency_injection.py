import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
def test_global_dependency_injection(benchmark):
    r = get("/sync/global_di")
    assert r.status_code == 200
    assert r.text == "GLOBAL DEPENDENCY"


@pytest.mark.benchmark
def test_router_dependency_injection(benchmark):
    r = get("/sync/router_di")
    assert r.status_code == 200
    assert r.text == "ROUTER DEPENDENCY"


@pytest.mark.benchmark
def test_subrouter_global_dependency_injection(benchmark):
    r = get("/di_subrouter/subrouter_global_di")
    assert r.status_code == 200
    assert r.text == "GLOBAL DEPENDENCY"


@pytest.mark.benchmark
def test_subrouter_router_dependency_injection(benchmark):
    r = get("/di_subrouter/subrouter_router_di")
    assert r.status_code == 200
    assert r.text == "ROUTER DEPENDENCY"
