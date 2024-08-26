from dataclasses import asdict, dataclass, field
import inspect
from inspect import Signature
from importlib import resources
from typing import Callable, Optional, TypedDict, List, Dict

from robyn.responses import FileResponse, html


@dataclass
class Contact:
    """
    The contact information for the exposed API.
    (https://swagger.io/specification/#contact-object)

    @param name: Optional[str] The identifying name of the contact person/organization.
    @param url: Optional[str] The URL pointing to the contact information. This MUST be in the form of a URL.
    @param email: Optional[str] The email address of the contact person/organization. This MUST be in the form of an email address.
    """

    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@dataclass
class License:
    """
    The license information for the exposed API.
    (https://swagger.io/specification/#license-object)

    @param name: Optional[str] The license name used for the API.
    @param url: Optional[str] A URL to the license used for the API. This MUST be in the form of a URL.
    """

    name: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Server:
    """
    An array of Server Objects, which provide connectivity information to a target server. If the servers property is
    not provided, or is an empty array, the default value would be a Server Object with a url value of /.
    (https://swagger.io/specification/#server-object)

    @param url: str A URL to the target host. This URL supports Server Variables and MAY be relative,
    to indicate that the host location is relative to the location where the OpenAPI document is being served.
    Variable substitutions will be made when a variable is named in {brackets}.
    @param description: Optional[str] An optional string describing the host designated by the URL.
    """

    url: str
    description: Optional[str] = None


@dataclass
class ExternalDocumentation:
    """
    Additional external documentation for this operation.
    (https://swagger.io/specification/#external-documentation-object)

    @param description: Optional[str] A description of the target documentation.
    @param url: Optional[str] The URL for the target documentation.
    """

    description: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Components:
    """
    Additional external documentation for this operation.
    (https://swagger.io/specification/#components-object)

    @param schemas: Optional[Dict[str, Dict]] An object to hold reusable Schema Objects.
    @param responses: Optional[Dict[str, Dict]] An object to hold reusable Response Objects.
    @param parameters: Optional[Dict[str, Dict]] An object to hold reusable Parameter Objects.
    @param examples: Optional[Dict[str, Dict]] An object to hold reusable Example Objects.
    @param requestBodies: Optional[Dict[str, Dict]] An object to hold reusable Request Body Objects.
    @param securitySchemes: Optional[Dict[str, Dict]] An object to hold reusable Security Scheme Objects.
    @param links: Optional[Dict[str, Dict]] An object to hold reusable Link Objects.
    @param callbacks: Optional[Dict[str, Dict]] An object to hold reusable Callback Objects.
    @param pathItems: Optional[Dict[str, Dict]] An object to hold reusable Callback Objects.
    """

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
    """
    Provides metadata about the API. The metadata MAY be used by tooling as required.
    (https://swagger.io/specification/#info-object)

    @param title: str The title of the API.
    @param version: str The version of the API.
    @param description: Optional[str] A description of the API.
    @param termsOfService: Optional[str] A URL to the Terms of Service for the API.
    @param contact: Contact The contact information for the exposed API.
    @param license: License The license information for the exposed API.
    @param servers: list[Server] An list of Server objects representing the servers.
    @param externalDocs: Optional[ExternalDocumentation] Additional external documentation.
    @param components: Components An element to hold various schemas for the document.
    """

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
    """
    This is the root object of the OpenAPI document.

    @param info: OpenAPIInfo Provides metadata about the API.
    @param openapi_spec: dict The content of openapi.json as a dict
    """

    info: OpenAPIInfo = field(default_factory=OpenAPIInfo)
    openapi_spec: dict = field(init=False)

    def __post_init__(self):
        """
        Initializes the openapi_spec dict
        """
        self.openapi_spec = {
            "openapi": "3.1.0",
            "info": asdict(self.info),
            "paths": {},
            "components": asdict(self.info.components),
            "servers": [asdict(server) for server in self.info.servers],
            "externalDocs": asdict(self.info.externalDocs) if self.info.externalDocs.url else None,
        }

    def add_openapi_path_obj(self, route_type: str, endpoint: str, openapi_name: str, openapi_tags: List[str], handler: Callable):
        """
        Adds the given path to openapi spec

        @param route_type: str the http method as string (get, post ...)
        @param endpoint: str the endpoint to be added
        @param openapi_name: str the name of the endpoint
        @param openapi_tags: List[str] for grouping of endpoints
        @param handler: Callable the handler function for the endpoint
        """

        query_params = None
        signature = inspect.signature(handler)
        openapi_description = inspect.getdoc(handler) or ""

        if signature and "query_params" in signature.parameters:
            query_params = signature.parameters["query_params"].default

        return_annotation = signature.return_annotation

        return_type = "text/plain" if return_annotation == Signature.empty or return_annotation is str else "application/json"

        modified_endpoint, path_obj = self.get_path_obj(endpoint, openapi_name, openapi_description, openapi_tags, query_params, return_type)

        if modified_endpoint not in self.openapi_spec["paths"]:
            self.openapi_spec["paths"][modified_endpoint] = {}
        self.openapi_spec["paths"][modified_endpoint][route_type] = path_obj

    def add_subrouter_paths(self, subrouter_openapi: "OpenAPI"):
        """
        Adds the subrouter paths to main router's openapi specs

        @param subrouter_openapi: OpenAPI the OpenAPI object of the current subrouter
        """
        paths = subrouter_openapi.openapi_spec["paths"]

        for path in paths:
            self.openapi_spec["paths"][path] = paths[path]

    def get_path_obj(self, endpoint: str, name: str, description: str, tags: List[str], query_params: Optional[TypedDict], return_type: str) -> (str, dict):
        """
        Get the "path" openapi object according to spec

        @param endpoint: str the endpoint to be added
        @param name: str the name of the endpoint
        @param description: Optional[str] short description of the endpoint (to be fetched from the endpoint defenition by default)
        @param tags: List[str] for grouping of endpoints
        @param query_params: Optional[TypedDict] query params for the function
        @param return_type: str return type of the endpoint handler

        @return: (str, dict) a tuple containing the endpoint with path params wrapped in braces and the "path" openapi object
        according to spec
        """
        # robyn has paths like /:url/:etc whereas openapi requires path like /{url}/{path}
        # this function is used for converting path params to the required form
        # initialized with endpoint for handling endpoints without path params
        endpoint_with_path_params_wrapped_in_braces = endpoint

        endpoint_path_params_split = endpoint.split(":")
        openapi_parameter_object = []

        if len(endpoint_path_params_split) > 1:
            endpoint_without_path_params = endpoint_path_params_split[0]

            endpoint_with_path_params_wrapped_in_braces = (
                endpoint_without_path_params[:-1] if endpoint_without_path_params.endswith("/") else endpoint_without_path_params
            )

            for path_param in endpoint_path_params_split[1:]:
                path_param_name = path_param[:-1] if path_param.endswith("/") else path_param

                openapi_parameter_object.append(
                    {
                        "name": path_param_name,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                )
                endpoint_with_path_params_wrapped_in_braces += "/{" + path_param_name + "}"

        if query_params:
            for query_param in query_params.__annotations__:
                query_param_type = self.get_openapi_type(query_params.__annotations__[query_param])

                openapi_parameter_object.append(
                    {
                        "name": query_param,
                        "in": "query",
                        "required": False,
                        "schema": {"type": query_param_type},
                    }
                )

        if not description:
            description = "No description provided"

        return endpoint_with_path_params_wrapped_in_braces, {
            "summary": name,
            "description": description,
            "tags": tags,
            "parameters": openapi_parameter_object,
            "responses": {"200": {"description": "Successful Response", "content": {return_type: {"schema": {}}}}},
        }

    def get_openapi_type(self, typed_dict: TypedDict) -> str:
        """
        Get actual type from the TypedDict annotations

        @param typed_dict: TypedDict The TypedDict to be converted
        @return: str the type inferred
        """
        type_mapping = {
            int: "integer",
            str: "string",
            bool: "boolean",
            float: "number",
            dict: "object",
            list: "array",
        }

        for type_name in type_mapping:
            if typed_dict is type_name:
                return type_mapping[type_name]

        # default to "string" if type is not found
        return "string"

    def get_openapi_docs_page(self) -> FileResponse:
        """
        Handler to the swagger html page to be deployed to the endpoint `/docs`
        @return: FileResponse the swagger html page
        """
        with resources.open_text("robyn", "swagger.html") as path:
            html_file = path.read()
        return html(html_file)

    def get_openapi_config(self) -> dict:
        """
        Returns the openapi spec as a dict
        @return: dict the openapi spec
        """
        return self.openapi_spec
