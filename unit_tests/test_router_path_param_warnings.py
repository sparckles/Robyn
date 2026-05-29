import logging

import pytest

from robyn.robyn import HttpMethod, Request
from robyn.router import Router
from robyn.types import PathParams


def add_get_route(router, endpoint, handler):
    router.add_route(
        route_type=HttpMethod.GET,
        endpoint=endpoint,
        handler=handler,
        is_const=False,
        auth_required=False,
        openapi_name="",
        openapi_tags=[],
        exception_handler=None,
        injected_dependencies={"router_dependencies": {}, "global_dependencies": {}},
    )


def path_param_warning_messages(caplog):
    return [record.getMessage() for record in caplog.records if record.name == "robyn.router" and "declares path params" in record.getMessage()]


def handler_with_request_name(request):
    return request


def handler_with_req_name(req):
    return req


def handler_with_r_name(r):
    return r


def handler_with_path_params_name(path_params):
    return path_params


def handler_with_path_param_name(key_id):
    return key_id


def handler_with_typed_request(request_data: Request):
    return request_data


def handler_with_typed_path_params(path_data: PathParams):
    return path_data


def handler_with_typed_request_and_named_param(request_data: Request, user_id):
    return request_data, user_id


@pytest.mark.parametrize(
    "handler",
    [
        handler_with_request_name,
        handler_with_req_name,
        handler_with_r_name,
        handler_with_path_params_name,
        handler_with_path_param_name,
        handler_with_typed_request,
        handler_with_typed_path_params,
    ],
)
def test_path_param_warning_skipped_for_request_or_path_params_access(caplog, handler):
    caplog.set_level(logging.WARNING, logger="robyn.router")

    add_get_route(Router(), "/v1/keys/:key_id", handler)

    assert path_param_warning_messages(caplog) == []


def test_path_param_warning_skipped_when_request_can_access_remaining_params(caplog):
    caplog.set_level(logging.WARNING, logger="robyn.router")

    add_get_route(Router(), "/users/:user_id/posts/:post_id", handler_with_typed_request_and_named_param)

    assert path_param_warning_messages(caplog) == []


def test_path_param_warning_logged_when_param_is_not_accessible(caplog):
    def handler():
        return "ok"

    caplog.set_level(logging.WARNING, logger="robyn.router")

    add_get_route(Router(), "/users/:user_id/posts/:post_id", handler)

    warning_messages = path_param_warning_messages(caplog)

    assert len(warning_messages) == 1
    assert "Route '/users/:user_id/posts/:post_id' declares path params" in warning_messages[0]
    assert "user_id" in warning_messages[0]
    assert "post_id" in warning_messages[0]
    assert "handler 'handler' doesn't use them" in warning_messages[0]
