import json
import os
import re
from dataclasses import dataclass, field, asdict
from inspect import Signature
from typing import List, Dict, TypedDict, Optional

import robyn


@dataclass
class Contact:
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@dataclass
class License:
    name: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Server:
    url: str
    description: Optional[str] = None


@dataclass
class ExternalDocumentation:
    description: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Components:
    schemas: Optional[Dict[str, Dict]] = field(default_factory=dict)
    responses: Optional[Dict[str, Dict]] = field(default_factory=dict)
    parameters: Optional[Dict[str, Dict]] = field(default_factory=dict)
    examples: Optional[Dict[str, Dict]] = field(default_factory=dict)
    requestBodies: Optional[Dict[str, Dict]] = field(default_factory=dict)
    securitySchemes: Optional[Dict[str, Dict]] = field(default_factory=dict)
    links: Optional[Dict[str, Dict]] = field(default_factory=dict)
    callbacks: Optional[Dict[str, Dict]] = field(default_factory=dict)
    pathItems: Optional[Dict[str, Dict]] = field(default_factory=dict)


@dataclass
class OpenAPIInfo:
    title: str = "Robyn API"
    version: str = "1.0.0"
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Contact = field(default_factory=Contact)
    license: License = field(default_factory=License)
    servers: List[Server] = field(default_factory=list)
    externalDocs: Optional[ExternalDocumentation] = field(default_factory=ExternalDocumentation)
    components: Components = field(default_factory=Components)


@dataclass
class OpenAPI:
    info: OpenAPIInfo = field(default_factory=OpenAPIInfo)
    openapi_spec: dict = field(init=False)

    def __post_init__(self):
        self.openapi_spec = {
            "openapi": "3.0.0",
            "info": asdict(self.info),
            "paths": {},
            "components": asdict(self.info.components),
            "servers": [asdict(server) for server in self.info.servers],
            "externalDocs": asdict(self.info.externalDocs) if self.info.externalDocs.url else None,
        }

    def add_openapi_path_obj(self, route_type: str, endpoint: str, openapi_summary: str, openapi_tags: list, signature: Signature = None):
        """
        adds the given path to openapi spec

        :param route_type: the http method as string (get, post ...)
        :param endpoint: the endpoint to be added
        :param openapi_summary: short summary of the endpoint (to be fetched from the endpoint defenition by default)
        :param openapi_tags: tags -- for grouping of endpoints
        :param signature: the function signature -- to grab the typed dict annotations for query params
        """

        query_params = None

        if "query_params" in signature.parameters:
            query_params = signature.parameters["query_params"].default

        modified_endpoint, path_obj = self.get_path_obj(endpoint, openapi_summary, openapi_tags, query_params)

        if modified_endpoint not in self.openapi_spec["paths"]:
            self.openapi_spec["paths"][modified_endpoint] = {}
        self.openapi_spec["paths"][modified_endpoint][route_type] = path_obj

    def add_subrouter_paths(self, subrouter_openapi):
        """

        adds the subrouter paths to main router's openapi specs

        :param subrouter_openapi: the OpenAPI object of the current subrouter
        """
        paths = subrouter_openapi.openapi_spec["paths"]

        for path in paths:
            self.openapi_spec["paths"][path] = paths[path]

    def get_path_obj(self, endpoint: str, summary: str, tags: list, query_params: TypedDict = None):
        """
        get the "path" openapi object according to spec

        :param endpoint: the endpoint to be added
        :param summary: short summary of the endpoint (to be fetched from the endpoint defenition by default)
        :param tags: tags -- for grouping of endpoints
        :param query_params: query params for the function

        :return: the "path" openapi object according to spec
        """
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
                        "required": True,  # should handle this too.
                        "schema": {"type": "string"},
                    }
                )
                modified_endpoint += "/{" + param_name + "}"

        if query_params:
            for query_param in query_params.__annotations__:
                # ugly hack -- should fix!
                param_type = re.findall("'[a-z]+'", str(query_params.__annotations__[query_param]))[0].replace("'", "")

                parameters.append(
                    {
                        "name": query_param,
                        "in": "query",
                        "required": False,
                        "schema": {"type": param_type},
                    }
                )

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
        """
        get the swagger html page
        @return: the swagger html page
        """
        json.dumps(self.openapi_spec)
        html_file = os.path.join(os.getcwd(), "robyn/swagger.html")
        return robyn.serve_html(html_file)

    def json_handler(self):
        """
        get the openapi spec json object
        @return: the openapi spec json object
        """
        return json.dumps(self.openapi_spec)
