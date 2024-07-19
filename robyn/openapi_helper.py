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
    component_schemas=None,
    component_responses=None,
    component_parameters=None,
    component_examples=None,
    component_request_bodies=None,
    component_security_schemes=None,
    component_links=None,
    component_callbacks=None,
    component_path_items=None,
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

    openapi_object["components"] = {}

    if component_schemas:
        openapi_object["components"]["schemas"] = component_schemas

    if component_responses:
        openapi_object["components"]["responses"] = component_responses

    if component_parameters:
        openapi_object["components"]["parameters"] = component_parameters

    if component_examples:
        openapi_object["components"]["examples"] = component_examples

    if component_request_bodies:
        openapi_object["components"]["requestBodies"] = component_request_bodies

    if component_security_schemes:
        openapi_object["components"]["securitySchemes"] = component_security_schemes

    if component_links:
        openapi_object["components"]["links"] = component_links

    if component_callbacks:
        openapi_object["components"]["callbacks"] = component_callbacks

    if component_path_items:
        openapi_object["components"]["pathItems"] = component_path_items

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
