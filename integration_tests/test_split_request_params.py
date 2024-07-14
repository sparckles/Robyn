import pytest

from integration_tests.helpers.http_methods_helpers import get, post


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_split_request_params_get_query_params(session, function_type):
    r = get(f"/{function_type}/split_request/query_params?hello=robyn")
    assert r.json() == {"hello": ["robyn"]}
    r = get(f"/{function_type}/split_request/query_params?hello=robyn&a=1&b=2")
    assert r.json() == {"hello": ["robyn"], "a": ["1"], "b": ["2"]}
    r = get(f"/{function_type}/split_request/query_params")
    assert r.json() == {}


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_split_request_params_get_headers(session, function_type):
    r = get(f"/{function_type}/split_request/headers")
    assert r.text == "robyn"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_split_request_params_get_path_params(session, function_type):
    r = get(f"/{function_type}/split_request/path_params/123")
    assert r.json() == {"id": "123"}


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_split_request_params_get_method(session, function_type):
    r = get(f"/{function_type}/split_request/method")
    assert r.text == "GET"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_split_request_params_get_body(session, function_type):
    res = post(f"/{function_type}/split_request/body", data={"hello": "world"})
    assert res.text == "hello=world"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_split_request_params_get_combined(session, function_type):
    res = post(
        f"/{function_type}/split_request/combined?hello=robyn&a=1&b=2",
        data={"hello": "world"},
    )
    out = res.json()
    assert out["query_params"] == {"hello": ["robyn"], "a": ["1"], "b": ["2"]}
    assert out["body"] == "hello=world"
    assert out["method"] == "POST"
    assert out["url"] == f"/{function_type}/split_request/combined"
    assert out["headers"] == "robyn"
