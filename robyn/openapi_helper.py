from typing import List, Dict, Union, Any


def build_schema(
    title: str = None,
    summary: str = None,
    description: str = None,
    terms_of_service: str = None,
    version: str = None,
    contact_name: str = None,
    contact_email: str = None,
    contact_url: str = None,
    license_name: str = None,
    license_url: str = None,
    servers: List[Dict[str, Union[str, Any]]] = None,
    external_docs: Dict[str, str] = None,
) -> {}:
    openapi_info_object = {}

    if title:
        openapi_info_object["title"] = title
    if summary:
        openapi_info_object["summary"] = summary
    if description:
        openapi_info_object["description"] = description
    if terms_of_service:
        openapi_info_object["termsOfService"] = terms_of_service
    if version:
        openapi_info_object["version"] = version

    openapi_info_object["contact"] = {}

    if contact_name:
        openapi_info_object["contact"]["name"] = contact_name
    if contact_email:
        openapi_info_object["contact"]["email"] = contact_email
    if contact_url:
        openapi_info_object["contact"]["url"] = contact_url

    openapi_info_object["license"] = {}

    if license_name:
        openapi_info_object["license"]["name"] = license_name
    if license_url:
        openapi_info_object["license"]["url"] = license_url

    openapi_object = {
        "openapi": "3.0.0",
        "info": openapi_info_object,
        "paths": {},
    }

    if servers:
        openapi_object["servers"] = servers

    if external_docs:
        openapi_object["externalDocs"] = external_docs

    return openapi_object


def get_path_obj(endpoint: str, summary: str, tags: list):
    modified_endpoint = endpoint

    path_params = endpoint.split(":")
    parameters = []

    if len(path_params) > 1:
        path = path_params[0]

        modified_endpoint = path[:-1] if path.endswith("/") else path

        for param in path_params[1:]:
            param_name = param[:-1] if param.endswith("/") else param

            parameters.append(
                {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            )
            modified_endpoint += "/{" + param_name + "}"

    return modified_endpoint, {
        "summary": summary,
        "tags": tags,
        "parameters": parameters,
        "responses": {
            "200": {
                "description": "Successful Response",
            }
        },
    }
