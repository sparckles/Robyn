import typing

from robyn.openapi import OpenAPI


def test_schema_basic_types():
    api = OpenAPI()
    assert api.get_schema_object("test", int) == {"title": "Test", "type": "integer"}
    assert api.get_schema_object("test", str) == {"title": "Test", "type": "string"}
    assert api.get_schema_object("test", bool) == {"title": "Test", "type": "boolean"}
    assert api.get_schema_object("test", float) == {"title": "Test", "type": "number"}
    assert api.get_schema_object("test", dict) == {"title": "Test", "type": "object"}
    assert api.get_schema_object("test", list) == {"title": "Test", "type": "array"}


def test_schema_typing_list():
    api = OpenAPI()
    schema = api.get_schema_object("test", typing.List[str])
    assert schema["type"] == "array"
    assert schema["items"] == {"title": "Test_item", "type": "string"}


def test_schema_builtin_generic_list():
    api = OpenAPI()
    schema = api.get_schema_object("test", list[int])
    assert schema["type"] == "array"
    assert schema["items"] == {"title": "Test_item", "type": "integer"}


def test_schema_list_of_custom_class():
    class Item:
        name: str
        count: int

    api = OpenAPI()
    schema = api.get_schema_object("test", typing.List[Item])
    assert schema["type"] == "array"
    assert schema["items"]["type"] == "object"
    assert "name" in schema["items"]["properties"]
    assert "count" in schema["items"]["properties"]


def test_schema_optional_primitive():
    api = OpenAPI()
    schema = api.get_schema_object("test", typing.Optional[str])
    assert "anyOf" in schema
    assert {"type": "string"} in schema["anyOf"]
    assert {"type": "null"} in schema["anyOf"]


def test_schema_optional_custom_class():
    class Widget:
        label: str

    api = OpenAPI()
    schema = api.get_schema_object("test", typing.Optional[Widget])
    assert "anyOf" in schema
    assert {"type": "null"} in schema["anyOf"]
    non_null = [s for s in schema["anyOf"] if s != {"type": "null"}]
    assert len(non_null) == 1
    assert non_null[0]["type"] == "object"
    assert "label" in non_null[0]["properties"]


def test_schema_union_multiple_primitives():
    api = OpenAPI()
    schema = api.get_schema_object("test", typing.Union[str, int])
    assert "anyOf" in schema
    assert {"type": "string"} in schema["anyOf"]
    assert {"type": "integer"} in schema["anyOf"]
    assert {"type": "null"} not in schema["anyOf"]


def test_schema_union_nullable_multiple():
    api = OpenAPI()
    schema = api.get_schema_object("test", typing.Union[str, int, None])
    assert "anyOf" in schema
    assert {"type": "string"} in schema["anyOf"]
    assert {"type": "integer"} in schema["anyOf"]
    assert {"type": "null"} in schema["anyOf"]


def test_schema_pep604_union():
    api = OpenAPI()
    schema = api.get_schema_object("test", str | int)
    assert "anyOf" in schema
    assert {"type": "string"} in schema["anyOf"]
    assert {"type": "integer"} in schema["anyOf"]


def test_schema_pep604_optional():
    api = OpenAPI()
    schema = api.get_schema_object("test", str | None)
    assert "anyOf" in schema
    assert {"type": "string"} in schema["anyOf"]
    assert {"type": "null"} in schema["anyOf"]


def test_schema_nested_optional_list():
    api = OpenAPI()
    schema = api.get_schema_object("test", typing.Optional[typing.List[str]])
    assert "anyOf" in schema
    assert {"type": "null"} in schema["anyOf"]
    non_null = [s for s in schema["anyOf"] if s != {"type": "null"}]
    assert len(non_null) == 1
    assert non_null[0]["type"] == "array"
    assert non_null[0]["items"]["type"] == "string"


def test_schema_custom_class():
    class MyModel:
        name: str
        age: int

    api = OpenAPI()
    schema = api.get_schema_object("test", MyModel)
    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"
