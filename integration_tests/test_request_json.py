import pytest

from integration_tests.helpers.http_methods_helpers import post


@pytest.mark.parametrize(
    "route, body, expected_result",
    [
        ("/sync/request_json", '{"hello": "world"}', "<class 'dict'>"),
        ("/sync/request_json/key", '{"key": "world"}', "world"),
        ("/sync/request_json", '{"hello": "world"', "None"),
        ("/async/request_json", '{"hello": "world"}', "<class 'dict'>"),
        ("/async/request_json", '{"hello": "world"', "None"),
        ("/sync/request_json/json_type", '{"start": null}', '{"start":null}'),  # null
        ("/sync/request_json/json_type", '{"lid":570}', '{"lid":570}'),  # number
        ("/sync/request_json/json_type", '{"lid":-570}', '{"lid":-570}'),  # number
        ("/sync/request_json/json_type", '{"lid":570.12}', '{"lid":570.12}'),  # number
        # string numeric literal
        ("/sync/request_json/json_type", '{"field_value": "111000111"}', '{"field_value":"111000111"}'),
        ("/sync/request_json/json_type", '{"field_name": "mobile"}', '{"field_name":"mobile"}'),  # string
        ("/sync/request_json/json_type", "[]", "[]"),  # empty Array
        ("/sync/request_json/json_type", "{}", "{}"),  # empty object
        ("/sync/request_json/json_type", '"string"', '"string"'),  # string only
        ("/sync/request_json/json_type", "570", "570"),  # number only
        ("/sync/request_json/json_type", '[{"k":"v"},{"k":null}]', '[{"k":"v"},{"k":null}]'),  # object Array
    ],
)
def test_request(route, body, expected_result):
    res = post(route, body)
    assert res.text == expected_result
