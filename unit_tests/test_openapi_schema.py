import typing

from robyn.openapi import OpenAPI


def test_schema_basic_types():
    api = OpenAPI()
    assert api.get_schema_object("test", int)["type"] == "integer"
    assert api.get_schema_object("test", str)["type"] == "string"
    assert api.get_schema_object("test", bool)["type"] == "boolean"
    assert api.get_schema_object("test", float)["type"] == "number"


def test_schema_list_type():
    api = OpenAPI()
    schema = api.get_schema_object("test", typing.List[str])
    assert schema["type"] == "array"
    assert "items" in schema


def test_schema_optional_type():
    api = OpenAPI()
    schema = api.get_schema_object("test", typing.Optional[str])
    assert "anyOf" in schema


def test_schema_custom_class():
    class MyModel:
        name: str
        age: int

    api = OpenAPI()
    schema = api.get_schema_object("test", MyModel)
    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
