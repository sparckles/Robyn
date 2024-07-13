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


@pytest.mark.benchmark
def test_subrouter_nested_1(benchmark):
    r = get("/di_subrouter/main-nest/nested-1/nested-2/nested-3/nested-route-3")
    assert r.status_code == 200
    assert r.text == "This is a route inside nested_router_3."


@pytest.mark.benchmark
def test_subrouter_nested_2(benchmark):
    r = get("/di_subrouter/main-nest/nested-1/nested-2/nested-3/nested-4/nested-route-4")
    assert r.status_code == 200
    assert r.text == "This is a route inside nested_router_4."


@pytest.mark.benchmark
def test_subrouter_nested_3(benchmark):
    r = get("/di_subrouter/main-nest/nested-1/nested-2/nested-3/nested-4/nested-5/nested-route-5")
    assert r.status_code == 200
    assert r.text == "This is a route inside nested_router_5."
