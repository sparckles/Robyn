import json
import os
from typing import List, Dict, Union, Any

from robyn import serve_html


class OpenAPI:
    def __init__(
        self,
        openapi_title: str = "Robyn",
        openapi_summary: str = None,
        openapi_description: str = None,
        openapi_terms_of_service: str = None,
        openapi_version: str = None,
        openapi_contact_name: str = None,
        openapi_contact_email: str = None,
        openapi_contact_url: str = None,
        openapi_license_name: str = None,
        openapi_license_url: str = None,
        openapi_servers: List[Dict[str, Union[str, Any]]] = None,
        openapi_external_docs: Dict[str, str] = None,
        openapi_component_schemas=None,
        openapi_component_responses=None,
        openapi_component_parameters=None,
        openapi_component_examples=None,
        openapi_component_request_bodies=None,
        openapi_component_security_schemes=None,
        openapi_component_links=None,
        openapi_component_callbacks=None,
        openapi_component_path_items=None,
    ):
        self.openapi_schema = self.build_schema(
            title=openapi_title,
            summary=openapi_summary,
            description=openapi_description,
            terms_of_service=openapi_terms_of_service,
            version=openapi_version,
            contact_name=openapi_contact_name,
            contact_email=openapi_contact_email,
            contact_url=openapi_contact_url,
            license_name=openapi_license_name,
            license_url=openapi_license_url,
            servers=openapi_servers,
            external_docs=openapi_external_docs,
            component_schemas=openapi_component_schemas,
            component_responses=openapi_component_responses,
            component_parameters=openapi_component_parameters,
            component_examples=openapi_component_examples,
            component_request_bodies=openapi_component_request_bodies,
            component_security_schemes=openapi_component_security_schemes,
            component_links=openapi_component_links,
            component_callbacks=openapi_component_callbacks,
            component_path_items=openapi_component_path_items,
        )

    def build_schema(
        self,
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

    def add_openapi_path_obj(self, route_type, endpoint, openapi_summary, openapi_tags):
        modified_endpoint, path_obj = self.get_path_obj(endpoint, openapi_summary, openapi_tags)

        if modified_endpoint not in self.openapi_schema["paths"]:
            self.openapi_schema["paths"][modified_endpoint] = {}
        self.openapi_schema["paths"][modified_endpoint][route_type] = path_obj

    def add_subrouter_paths(self, subrouter_openapi):
        paths = subrouter_openapi.openapi_schema["paths"]

        for path in paths:
            self.openapi_schema["paths"][path] = paths[path]

    def get_path_obj(self, endpoint: str, summary: str, tags: list):
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

    def docs_handler(self):
        json.dumps(self.openapi_schema)
        html_file = os.path.join(os.getcwd(), "robyn/swagger.html")
        return serve_html(html_file)

    def json_handler(self):
        return json.dumps(self.openapi_schema)


openapi = OpenAPI()
