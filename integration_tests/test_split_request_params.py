import pytest

from integration_tests.helpers.http_methods_helpers import get, post


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize("type_route", ["split_request_untyped", "split_request_typed"])
def test_split_request_params_get_query_params(session, type_route, function_type):
    r = get(f"/{function_type}/{type_route}/query_params?hello=robyn")
    assert r.json() == {"hello": ["robyn"]}
    r = get(f"/{function_type}/{type_route}/query_params?hello=robyn&a=1&b=2")
    assert r.json() == {"hello": ["robyn"], "a": ["1"], "b": ["2"]}
    r = get(f"/{function_type}/{type_route}/query_params")
    assert r.json() == {}


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize("type_route", ["split_request_untyped", "split_request_typed"])
def test_split_request_params_get_headers(session, type_route, function_type):
    r = get(f"/{function_type}/{type_route}/headers")
    assert r.text == "robyn"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize("type_route", ["split_request_untyped", "split_request_typed"])
def test_split_request_params_get_path_params(session, type_route, function_type):
    r = get(f"/{function_type}/{type_route}/path_params/123")
    assert r.json() == {"id": "123"}


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize("type_route", ["split_request_untyped", "split_request_typed"])
def test_split_request_params_get_method(session, type_route, function_type):
    r = get(f"/{function_type}/{type_route}/method")
    assert r.text == "GET"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize("type_route", ["split_request_untyped", "split_request_typed"])
def test_split_request_params_get_body(session, type_route, function_type):
    res = post(f"/{function_type}/{type_route}/body", data={"hello": "world"})
    assert res.text == "hello=world"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize("type_route", ["split_request_untyped", "split_request_typed"])
def test_split_request_params_get_combined(session, type_route, function_type):
    res = post(
        f"/{function_type}/{type_route}/combined?hello=robyn&a=1&b=2",
        data={"hello": "world"},
    )
    out = res.json()
    assert out["query_params"] == {"hello": ["robyn"], "a": ["1"], "b": ["2"]}
    assert out["body"] == "hello=world"
    assert out["method"] == "POST"
    assert out["url"] == f"/{function_type}/{type_route}/combined"
    assert out["headers"] == "robyn"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_split_request_params_typed_untyped_post_combined(session, function_type):
    res = post(
        f"/{function_type}/split_request_typed_untyped/combined?hello=robyn&a=1&b=2",
        data={"hello": "world"},
    )
    out = res.json()
    assert out["query_params"] == {"hello": ["robyn"], "a": ["1"], "b": ["2"]}
    assert out["body"] == "hello=world"
    assert out["method"] == "POST"
    assert out["url"] == f"/{function_type}/split_request_typed_untyped/combined"
    assert out["headers"] == "robyn"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_split_request_params_get_combined_failure(session, function_type):
    res = post(f"/{function_type}/split_request_typed_untyped/combined/failure?hello=robyn&a=1&b=2", data={"hello": "world"}, should_check_response=False)
    assert 500 == res.status_code
