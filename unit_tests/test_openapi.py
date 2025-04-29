import datetime
from dataclasses import dataclass
from typing import Optional


from robyn.openapi import OpenAPI, OpenAPIInfo
from robyn.types import JSONResponse


@dataclass
class DateResponseModel(JSONResponse):
    date: datetime.datetime
    optional_date: Optional[datetime.date] = None


def test_datetime_schema_object():
    """Test the schema generation for datetime types"""
    openapi = OpenAPI(info=OpenAPIInfo())

    schema = openapi.get_schema_object("test", datetime.datetime)
    assert schema["type"] == "string"
    assert schema["format"] == "date-time"

    schema = openapi.get_schema_object("test", datetime.date)
    assert schema["type"] == "string"
    assert schema["format"] == "date"


def test_datetime_response_object():
    """Test the schema generation for response objects containing datetime fields"""
    openapi = OpenAPI(info=OpenAPIInfo())

    schema = openapi.get_schema_object("test", DateResponseModel)
    assert schema["type"] == "object"
    assert "properties" in schema
    assert schema["properties"]["date"]["type"] == "string"
    assert schema["properties"]["date"]["format"] == "date-time"
    assert schema["properties"]["optional_date"]["anyOf"] == [{"type": "string", "format": "date"}, {"type": "null"}]


def test_datetime_path_object():
    """Test the OpenAPI path object generation for datetime return types"""
    openapi = OpenAPI(info=OpenAPIInfo())

    _, path_obj = openapi.get_path_obj(
        endpoint="/test",
        name="Test Endpoint",
        description="Test description",
        tags=["test"],
        query_params=None,
        request_body=None,
        return_annotation=datetime.datetime,
    )

    assert path_obj["responses"]["200"]["content"]["application/json"]["schema"]["type"] == "string"
    assert path_obj["responses"]["200"]["content"]["application/json"]["schema"]["format"] == "date-time"

    _, path_obj = openapi.get_path_obj(
        endpoint="/test",
        name="Test Endpoint",
        description="Test description",
        tags=["test"],
        query_params=None,
        request_body=None,
        return_annotation=datetime.date,
    )

    assert path_obj["responses"]["200"]["content"]["application/json"]["schema"]["type"] == "string"
    assert path_obj["responses"]["200"]["content"]["application/json"]["schema"]["format"] == "date"
