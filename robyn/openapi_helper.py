import json
import os
import re

openapi_schema = {}


def extract_path_params(path: str):
    return re.findall(r"{(.*?)}", path)


def init_schema(schema):
    global openapi_schema
    openapi_schema = schema


def get_json_file():
    return json.dumps(openapi_schema)


def get_html_file():
    cwd = os.getcwd()
    html_file = os.path.join(cwd, "testing_application/swagger.html")

    return html_file


def add_openapi_route(path: str, method: str, summary: str, tags: list):
    if not path or not method or not summary or not tags:
        return

    if path not in openapi_schema["paths"]:
        openapi_schema["paths"][path] = {}

    path_params = extract_path_params(path)
    parameters = []
    for param in path_params:
        parameters.append(
            {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},  # You might need to adjust the type based on your API design.
            }
        )

    openapi_schema["paths"][path][method.lower()] = {
        "summary": summary,
        "tags": tags,
        "parameters": parameters,
        # requestBody and responses can be added here if needed
    }
