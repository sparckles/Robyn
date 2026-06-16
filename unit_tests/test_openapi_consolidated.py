"""Consolidated OpenAPI/Swagger tests.

Covers the behaviour added in the consolidated OpenAPI PR that closes:
  - #1124 (datetime/date return types crashing schema generation)
  - #1073 (container types not rendered in request bodies)
  - #1257 (multiple/additional responses)
  - #1122 / #1339 (empty Swagger "Authorize" popup + security schemes)
and the FastAPI-parity route flags status_code/deprecated/include_in_schema/
response_model/responses (superseding PRs #1368, #1369, #1370, #1373).
"""

import datetime
import decimal
import enum
import typing
import uuid

import pytest

from robyn.openapi import Components, OpenAPI, OpenAPIInfo, RouteOpenAPIMeta
from robyn.router import Router
from robyn.types import Body, JSONResponse


# --------------------------------------------------------------------------- #
# Schema generation for stdlib leaf types (#1124, #1073)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "py_type, expected",
    [
        (datetime.datetime, {"type": "string", "format": "date-time"}),
        (datetime.date, {"type": "string", "format": "date"}),
        (datetime.time, {"type": "string", "format": "time"}),
        (datetime.timedelta, {"type": "string", "format": "duration"}),
        (uuid.UUID, {"type": "string", "format": "uuid"}),
        (decimal.Decimal, {"type": "number"}),
        (bytes, {"type": "string", "format": "binary"}),
    ],
)
def test_schema_leaf_types(py_type, expected):
    api = OpenAPI()
    schema = api.get_schema_object("when", py_type)
    for key, value in expected.items():
        assert schema[key] == value


def test_schema_enum():
    class Color(enum.Enum):
        RED = "red"
        GREEN = "green"

    api = OpenAPI()
    schema = api.get_schema_object("color", Color)
    assert schema["type"] == "string"
    assert schema["enum"] == ["red", "green"]


def test_schema_int_enum():
    class Priority(enum.IntEnum):
        LOW = 1
        HIGH = 2

    api = OpenAPI()
    schema = api.get_schema_object("priority", Priority)
    assert schema["type"] == "integer"
    assert schema["enum"] == [1, 2]


def test_schema_literal():
    api = OpenAPI()
    schema = api.get_schema_object("mode", typing.Literal["a", "b", "c"])
    assert schema["enum"] == ["a", "b", "c"]
    assert schema["type"] == "string"


def test_schema_typed_dict_value():
    api = OpenAPI()
    schema = api.get_schema_object("meta", dict[str, int])
    assert schema["type"] == "object"
    assert schema["additionalProperties"]["type"] == "integer"


def test_schema_set_is_array():
    api = OpenAPI()
    schema = api.get_schema_object("tags", set[str])
    assert schema["type"] == "array"
    assert schema["items"]["type"] == "string"


def test_schema_any_has_no_type():
    api = OpenAPI()
    schema = api.get_schema_object("anything", typing.Any)
    assert "type" not in schema


def test_schema_body_with_containers_and_datetime():
    """A Body subclass mixing list/optional/datetime fields (#1073, #1124)."""

    class ActionItemsRequest(Body):
        action_items: str
        emails: list[str]
        meeting_summary: typing.Optional[str]
        scheduled_for: datetime.datetime

    api = OpenAPI()
    schema = api.get_schema_object("req", ActionItemsRequest)
    props = schema["properties"]
    assert props["emails"]["type"] == "array"
    assert props["emails"]["items"]["type"] == "string"
    assert "anyOf" in props["meeting_summary"]
    assert props["scheduled_for"] == {"title": "Scheduled_for", "type": "string", "format": "date-time"}


def test_datetime_return_annotation_does_not_crash():
    """Regression for #1124: a datetime return type used to crash startup."""

    def handler() -> datetime.datetime:
        """Returns now"""
        return datetime.datetime.now()

    api = OpenAPI()
    api.add_openapi_path_obj("get", "/now", "now", ["t"], handler)
    schema = api.openapi_spec["paths"]["/now"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["type"] == "string"
    assert schema["format"] == "date-time"


# --------------------------------------------------------------------------- #
# Per-route flags: status_code / deprecated / include_in_schema (#1368, #1369)
# --------------------------------------------------------------------------- #
def _path_obj(api, endpoint, handler, meta, auth_required=False):
    api.add_openapi_path_obj("get", endpoint, "name", ["t"], handler, auth_required=auth_required, meta=meta)
    return api.openapi_spec["paths"].get(endpoint, {}).get("get")


def test_status_code_sets_success_response_key():
    api = OpenAPI()

    def handler() -> dict:
        """h"""
        return {}

    obj = _path_obj(api, "/created", handler, RouteOpenAPIMeta(status_code=201))
    assert "201" in obj["responses"]
    assert "200" not in obj["responses"]


def test_deprecated_flag_in_spec():
    api = OpenAPI()

    def handler():
        """h"""

    obj = _path_obj(api, "/old", handler, RouteOpenAPIMeta(deprecated=True))
    assert obj["deprecated"] is True


def test_include_in_schema_false_omits_route():
    api = OpenAPI()

    def handler():
        """h"""

    obj = _path_obj(api, "/hidden", handler, RouteOpenAPIMeta(include_in_schema=False))
    assert obj is None
    assert "/hidden" not in api.openapi_spec["paths"]


def test_operation_id_in_spec():
    api = OpenAPI()

    def handler():
        """h"""

    obj = _path_obj(api, "/op", handler, RouteOpenAPIMeta(operation_id="get_op"))
    assert obj["operationId"] == "get_op"


# --------------------------------------------------------------------------- #
# Additional responses (#1257, #1373)
# --------------------------------------------------------------------------- #
def test_additional_responses_string_and_model():
    class ErrorResponse(JSONResponse):
        message: str

    api = OpenAPI()

    def handler() -> dict:
        """h"""
        return {}

    meta = RouteOpenAPIMeta(responses={404: "Not found", 422: {"description": "Invalid", "model": ErrorResponse}})
    obj = _path_obj(api, "/items", handler, meta)
    assert obj["responses"]["404"] == {"description": "Not found"}
    assert obj["responses"]["422"]["description"] == "Invalid"
    schema = obj["responses"]["422"]["content"]["application/json"]["schema"]
    assert "message" in schema["properties"]


def test_additional_responses_passthrough_object():
    api = OpenAPI()

    def handler() -> dict:
        """h"""
        return {}

    raw = {"description": "Teapot", "content": {"text/plain": {"schema": {"type": "string"}}}}
    obj = _path_obj(api, "/tea", handler, RouteOpenAPIMeta(responses={418: raw}))
    assert obj["responses"]["418"] == raw


# --------------------------------------------------------------------------- #
# response_model schema override (#1370)
# --------------------------------------------------------------------------- #
def test_response_model_overrides_return_annotation():
    class UserOut(JSONResponse):
        name: str
        age: int

    api = OpenAPI()

    def handler() -> str:
        """h"""
        return "ignored"

    api.add_openapi_path_obj("get", "/user", "user", ["t"], handler, meta=RouteOpenAPIMeta(response_model=UserOut))
    schema = api.openapi_spec["paths"]["/user"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]


# --------------------------------------------------------------------------- #
# Security schemes + components cleanup (#1122, #1339)
# --------------------------------------------------------------------------- #
def test_auth_required_emits_operation_security():
    api = OpenAPI(info=OpenAPIInfo(components=Components(securitySchemes={"BearerAuth": {"type": "http", "scheme": "bearer"}})))

    def handler():
        """h"""

    obj = _path_obj(api, "/secret", handler, RouteOpenAPIMeta(), auth_required=True)
    assert obj["security"] == [{"BearerAuth": []}]


def test_auth_required_without_scheme_has_no_security():
    api = OpenAPI()

    def handler():
        """h"""

    obj = _path_obj(api, "/secret", handler, RouteOpenAPIMeta(), auth_required=True)
    assert "security" not in obj


def test_prune_empty_components_removes_empty_security_schemes():
    api = OpenAPI()
    # Default spec ships an empty securitySchemes bucket that makes Swagger UI
    # render an empty Authorize popup.
    assert api.openapi_spec["components"]["securitySchemes"] == {}
    api.prune_empty_components()
    assert "securitySchemes" not in api.openapi_spec["components"]


def test_add_security_scheme_keeps_bucket_after_prune():
    api = OpenAPI()
    api.add_security_scheme("BearerAuth", {"type": "http", "scheme": "bearer"})
    api.prune_empty_components()
    assert api.openapi_spec["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"


# --------------------------------------------------------------------------- #
# Runtime application of response_model / status_code (Router helpers)
# --------------------------------------------------------------------------- #
def test_coerce_status_code_wraps_plain_dict():
    router = Router()
    resp = router._coerce_status_code({"a": 1}, 201)
    assert resp.status_code == 201


def test_coerce_status_code_respects_explicit_response():
    from robyn.robyn import Response

    router = Router()
    explicit = Response(status_code=204, headers={}, description="")
    resp = router._coerce_status_code(explicit, 201)
    assert resp.status_code == 204


def test_coerce_status_code_noop_when_none():
    router = Router()
    result = {"a": 1}
    assert router._coerce_status_code(result, None) is result


def test_apply_response_model_requires_pydantic():
    pydantic = pytest.importorskip("pydantic")

    class UserResponse(pydantic.BaseModel):
        name: str
        age: int

    router = Router()
    resp = router._apply_response_model({"name": "Alice", "age": 30, "extra": "dropped"}, UserResponse, 201)
    assert resp.status_code == 201
    assert b"Alice" in (resp.description if isinstance(resp.description, bytes) else resp.description.encode())
    assert "dropped" not in (resp.description if isinstance(resp.description, str) else resp.description.decode())
