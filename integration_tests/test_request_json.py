import pytest

from integration_tests.helpers.http_methods_helpers import json_patch, json_post, json_put, post


@pytest.mark.parametrize(
    "route, body, expected_result",
    [
        ("/sync/request_json", '{"hello": "world"}', "<class 'dict'>"),
        ("/sync/request_json/key", '{"key": "world"}', "world"),
        ("/sync/request_json", '{"hello": "world"', "None"),
        ("/async/request_json", '{"hello": "world"}', "<class 'dict'>"),
        ("/async/request_json", '{"hello": "world"', "None"),
    ],
)
def test_request(route, body, expected_result, session):
    res = post(route, body)
    assert res.text == expected_result


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_request_json_method_parity(function_type: str, session):
    payload = {
        "name": "robyn",
        "count": 3,
        "active": True,
        "metadata": {
            "tags": ["post", "put", "patch"],
            "optional": None,
        },
    }

    responses = [
        json_post(f"/{function_type}/request_json/echo", json_data=payload),
        json_put(f"/{function_type}/request_json/echo", json_data=payload),
        json_patch(f"/{function_type}/request_json/echo", json_data=payload),
    ]

    for response in responses:
        assert response.json() == payload
