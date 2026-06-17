import datetime
import decimal
import enum
import inspect
import json
import logging
import re
import types
import typing
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from importlib import resources
from inspect import Signature
from pathlib import Path
from typing import Any, TypedDict, get_args, get_origin, is_typeddict

from robyn.pydantic_support import get_pydantic_openapi_schema, is_pydantic_model
from robyn.responses import html
from robyn.robyn import QueryParams, Response
from robyn.types import Body, JsonBody

_logger = logging.getLogger(__name__)


class str_typed_dict(TypedDict):
    key: str
    value: str


@dataclass
class RouteOpenAPIMeta:
    """Per-route OpenAPI metadata captured from the route decorators.

    Bundles the familiar route-documentation knobs so handlers can document
    their behaviour without hand-writing the spec.

    @param status_code: int | None the default success status code (e.g. 201). Reflected
        both at runtime (for plain returns) and as the success response key in the spec.
    @param deprecated: bool marks the operation as deprecated (strikethrough in Swagger UI).
    @param include_in_schema: bool when False the route is omitted from the generated spec.
    @param response_model: Any a type (typically a Pydantic model) used as the success
        response schema, overriding the handler's return annotation.
    @param responses: dict | None additional responses keyed by status code. Each value may be
        a description string, a full OpenAPI response object, or a dict with a ``model`` key.
    @param summary: str | None overrides the operation summary (defaults to ``openapi_name``).
    @param description: str | None overrides the operation description (defaults to the docstring).
    @param operation_id: str | None an explicit ``operationId`` for the operation.
    """

    status_code: int | None = None
    deprecated: bool = False
    include_in_schema: bool = True
    response_model: Any = None
    responses: dict[int | str, Any] | None = None
    summary: str | None = None
    description: str | None = None
    operation_id: str | None = None


# Special leaf types that map to a JSON Schema ``type``/``format`` pair.
# Mirrors the representation Pydantic emits for these stdlib types so
# that a handler returning e.g. ``datetime`` produces a valid, descriptive
# schema instead of crashing or rendering as a bare object (see #1124, #1073).
_LEAF_TYPE_SCHEMAS: dict[type, dict] = {
    datetime.datetime: {"type": "string", "format": "date-time"},
    datetime.date: {"type": "string", "format": "date"},
    datetime.time: {"type": "string", "format": "time"},
    datetime.timedelta: {"type": "string", "format": "duration"},
    uuid.UUID: {"type": "string", "format": "uuid"},
    decimal.Decimal: {"type": "number"},
    bytes: {"type": "string", "format": "binary"},
}

# Primitive Python types and their JSON Schema ``type`` names.
_PRIMITIVE_TYPE_NAMES: dict[type, str] = {
    int: "integer",
    str: "string",
    bool: "boolean",
    float: "number",
    dict: "object",
    list: "array",
}


@dataclass
class Contact:
    """
    The contact information for the exposed API.
    (https://swagger.io/specification/#contact-object)

    @param name: str | None The identifying name of the contact person/organization.
    @param url: str | None The URL pointing to the contact information. This MUST be in the form of a URL.
    @param email: str | None The email address of the contact person/organization. This MUST be in the form of an email address.
    """

    name: str | None = None
    url: str | None = None
    email: str | None = None


@dataclass
class License:
    """
    The license information for the exposed API.
    (https://swagger.io/specification/#license-object)

    @param name: str | None The license name used for the API.
    @param url: str | None A URL to the license used for the API. This MUST be in the form of a URL.
    """

    name: str | None = None
    url: str | None = None


@dataclass
class Server:
    """
    An array of Server Objects, which provide connectivity information to a target server. If the servers property is
    not provided, or is an empty array, the default value would be a Server Object with a url value of /.
    (https://swagger.io/specification/#server-object)

    @param url: str A URL to the target host. This URL supports Server Variables and MAY be relative,
    to indicate that the host location is relative to the location where the OpenAPI document is being served.
    Variable substitutions will be made when a variable is named in {brackets}.
    @param description: str | None An optional string describing the host designated by the URL.
    """

    url: str
    description: str | None = None


@dataclass
class ExternalDocumentation:
    """
    Additional external documentation for this operation.
    (https://swagger.io/specification/#external-documentation-object)

    @param description: str | None A description of the target documentation.
    @param url: str | None The URL for the target documentation.
    """

    description: str | None = None
    url: str | None = None


@dataclass
class Components:
    """
    Additional external documentation for this operation.
    (https://swagger.io/specification/#components-object)

    @param schemas: dict[str, dict] | None An object to hold reusable Schema Objects.
    @param responses: dict[str, dict] | None An object to hold reusable Response Objects.
    @param parameters: dict[str, dict] | None An object to hold reusable Parameter Objects.
    @param examples: dict[str, dict] | None An object to hold reusable Example Objects.
    @param requestBodies: dict[str, dict] | None An object to hold reusable Request Body Objects.
    @param securitySchemes: dict[str, dict] | None An object to hold reusable Security Scheme Objects.
    @param links: dict[str, dict] | None An object to hold reusable Link Objects.
    @param callbacks: dict[str, dict] | None An object to hold reusable Callback Objects.
    @param pathItems: dict[str, dict] | None An object to hold reusable Callback Objects.
    """

    schemas: dict[str, dict] | None = field(default_factory=dict)
    responses: dict[str, dict] | None = field(default_factory=dict)
    parameters: dict[str, dict] | None = field(default_factory=dict)
    examples: dict[str, dict] | None = field(default_factory=dict)
    requestBodies: dict[str, dict] | None = field(default_factory=dict)
    securitySchemes: dict[str, dict] | None = field(default_factory=dict)
    links: dict[str, dict] | None = field(default_factory=dict)
    callbacks: dict[str, dict] | None = field(default_factory=dict)
    pathItems: dict[str, dict] | None = field(default_factory=dict)


@dataclass
class OpenAPIInfo:
    """
    Provides metadata about the API. The metadata MAY be used by tooling as required.
    (https://swagger.io/specification/#info-object)

    @param title: str The title of the API.
    @param version: str The version of the API.
    @param description: str | None A description of the API.
    @param termsOfService: str | None A URL to the Terms of Service for the API.
    @param contact: Contact The contact information for the exposed API.
    @param license: License The license information for the exposed API.
    @param servers: list[Server] An list of Server objects representing the servers.
    @param externalDocs: ExternalDocumentation | None Additional external documentation.
    @param components: Components An element to hold various schemas for the document.
    """

    title: str = "Robyn API"
    version: str = "1.0.0"
    description: str | None = None
    termsOfService: str | None = None
    contact: Contact = field(default_factory=Contact)
    license: License = field(default_factory=License)
    servers: list[Server] = field(default_factory=list)
    externalDocs: ExternalDocumentation | None = field(default_factory=ExternalDocumentation)
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
    openapi_file_override: bool = False  # denotes whether there is an override or not.

    def __post_init__(self):
        """
        Initializes the openapi_spec dict
        """
        if self.openapi_file_override:
            return

        self.openapi_spec = {
            "openapi": "3.1.0",
            "info": asdict(self.info),
            "paths": {},
            "components": asdict(self.info.components),
            "servers": [asdict(server) for server in self.info.servers],
            "externalDocs": asdict(self.info.externalDocs) if self.info.externalDocs.url else None,
        }

    def add_security_scheme(self, name: str, scheme: dict) -> None:
        """Register a reusable security scheme (e.g. Bearer/API-key auth).

        Populating ``components.securitySchemes`` is what makes Swagger UI's
        "Authorize" button appear and work; without it the button is either
        absent or opens an empty popup (see #1122, #1339).

        @param name: str the key under ``components.securitySchemes`` (e.g. ``"BearerAuth"``).
        @param scheme: dict the OpenAPI Security Scheme Object, e.g.
            ``{"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}``.
        """
        if self.openapi_file_override:
            return
        self.openapi_spec["components"].setdefault("securitySchemes", {})[name] = scheme

    @property
    def _security_scheme_names(self) -> list[str]:
        return list(self.openapi_spec.get("components", {}).get("securitySchemes", {}) or {})

    def prune_empty_components(self) -> None:
        """Drop empty ``components`` buckets so the generated spec stays clean.

        In particular an empty ``securitySchemes: {}`` makes Swagger UI render an
        empty "Available authorizations" popup; omitting it removes the button
        entirely until the user actually configures a scheme (#1122, #1339).
        """
        if self.openapi_file_override:
            return
        components = self.openapi_spec.get("components")
        if isinstance(components, dict):
            for key in list(components):
                if not components[key]:
                    del components[key]

    def add_openapi_path_obj(
        self,
        route_type: str,
        endpoint: str,
        openapi_name: str,
        openapi_tags: list[str],
        handler: Callable,
        auth_required: bool = False,
        meta: "RouteOpenAPIMeta | None" = None,
    ):
        """
        Adds the given path to openapi spec

        @param route_type: str the http method as string (get, post ...)
        @param endpoint: str the endpoint to be added
        @param openapi_name: str the name of the endpoint
        @param openapi_tags: list[str] for grouping of endpoints
        @param handler: Callable the handler function for the endpoint
        @param auth_required: bool whether the route requires authentication (adds a security requirement)
        @param meta: RouteOpenAPIMeta | None per-route OpenAPI metadata from the decorator
        """

        if self.openapi_file_override:
            return

        if meta is None:
            meta = RouteOpenAPIMeta()

        if not meta.include_in_schema:
            return

        query_params = None
        request_body = None
        return_annotation = None

        signature = inspect.signature(handler)
        openapi_description = inspect.getdoc(handler) or ""

        if signature:
            parameters = signature.parameters

            if "query_params" in parameters:
                query_params = parameters["query_params"].default

                if query_params is Signature.empty:
                    query_params = None

            if "body" in parameters:
                request_body = parameters["body"].default

                if request_body is Signature.empty:
                    request_body = None

            # priority to typing
            for parameter in parameters:
                param_annotation = parameters[parameter].annotation

                if inspect.isclass(param_annotation):
                    if issubclass(param_annotation, JsonBody):
                        request_body = param_annotation
                    elif issubclass(param_annotation, Body):
                        request_body = param_annotation
                    elif issubclass(param_annotation, QueryParams):
                        query_params = param_annotation
                    elif is_pydantic_model(param_annotation):
                        request_body = param_annotation
                    elif is_typeddict(param_annotation):
                        request_body = param_annotation

            if signature.return_annotation is not Signature.empty:
                return_annotation = signature.return_annotation

        # An explicit response_model wins over the handler's return annotation.
        if meta.response_model is not None:
            return_annotation = meta.response_model

        summary = meta.summary if meta.summary is not None else openapi_name
        description = meta.description if meta.description is not None else openapi_description

        modified_endpoint, path_obj = self.get_path_obj(
            endpoint,
            summary,
            description,
            openapi_tags,
            query_params,
            request_body,
            return_annotation,
            auth_required=auth_required,
            meta=meta,
        )

        if modified_endpoint not in self.openapi_spec["paths"]:
            self.openapi_spec["paths"][modified_endpoint] = {}
        self.openapi_spec["paths"][modified_endpoint][route_type] = path_obj

    def _merge_component_schemas(self, incoming: dict):
        """Merge incoming component schemas into the spec with collision detection.

        If an incoming schema name already exists and the schemas differ,
        a warning is logged.  The incoming schema always wins so that the
        most-recently-registered route's models are used (matching the
        behaviour of path registration).
        """
        existing = self.openapi_spec["components"]["schemas"]
        for name, schema in incoming.items():
            if name in existing and existing[name] != schema:
                _logger.warning(
                    "OpenAPI component schema '%s' is defined by multiple models with different shapes — the later definition will be used",
                    name,
                )
            existing[name] = schema

    def add_subrouter_paths(self, subrouter_openapi: "OpenAPI"):
        """
        Adds the subrouter paths and component schemas to main router's openapi specs.

        @param subrouter_openapi: OpenAPI the OpenAPI object of the current subrouter
        """

        if self.openapi_file_override:
            return

        for path, path_obj in subrouter_openapi.openapi_spec["paths"].items():
            self.openapi_spec["paths"][path] = path_obj

        subrouter_schemas = subrouter_openapi.openapi_spec.get("components", {}).get("schemas", {})
        if subrouter_schemas:
            self._merge_component_schemas(subrouter_schemas)

    def get_path_obj(
        self,
        endpoint: str,
        name: str,
        description: str,
        tags: list[str],
        query_params: str_typed_dict | None,
        request_body: str_typed_dict | None,
        return_annotation: str_typed_dict | None,
        auth_required: bool = False,
        meta: "RouteOpenAPIMeta | None" = None,
    ) -> tuple[str, dict]:
        """
        Get the "path" openapi object according to spec

        @param endpoint: str the endpoint to be added
        @param name: str the name of the endpoint
        @param description: str | None short description of the endpoint (to be fetched from the endpoint definition by default)
        @param tags: list[str] for grouping of endpoints
        @param query_params: TypedDict | None query params for the function
        @param request_body: TypedDict | None request body for the function
        @param return_annotation: TypedDict | None return type of the endpoint handler
        @param auth_required: bool whether the route requires authentication
        @param meta: RouteOpenAPIMeta | None per-route OpenAPI metadata (status_code, responses, ...)

        @return: (str, dict) a tuple containing the endpoint with path params wrapped in braces and the "path" openapi object
        according to spec
        """

        if meta is None:
            meta = RouteOpenAPIMeta()

        if not description:
            description = "No description provided"

        openapi_path_object: dict = {
            "summary": name,
            "description": description,
            "parameters": [],
            "tags": tags,
        }

        if meta.operation_id is not None:
            openapi_path_object["operationId"] = meta.operation_id

        if meta.deprecated:
            openapi_path_object["deprecated"] = True

        # auth_required routes advertise every configured security scheme so the
        # Swagger UI "Authorize" lock appears on them (#1122, #1339).
        if auth_required and self._security_scheme_names:
            openapi_path_object["security"] = [{scheme_name: []} for scheme_name in self._security_scheme_names]

        # robyn has paths like /:url/:etc whereas openapi requires path like /{url}/{path}
        # this function is used for converting path params to the required form
        # initialized with endpoint for handling endpoints without path params
        endpoint_with_path_params_wrapped_in_braces = endpoint

        path_param_names = re.findall(r":(\w+)", endpoint)

        if path_param_names:
            # Convert param syntax to OpenAPI's {param} syntax
            # \w+ matches word characters (letters, digits, underscores) and does not match '/',
            # so each :param is captured individually without swallowing intervening path segments.
            endpoint_with_path_params_wrapped_in_braces = re.sub(r":(\w+)", r"{\1}", endpoint)

            for name in path_param_names:
                openapi_path_object["parameters"].append(
                    {
                        "name": name,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                )

        if query_params:
            query_param_annotations = query_params.__annotations__ if query_params is str_typed_dict else typing.get_type_hints(query_params)

            for query_param in query_param_annotations:
                query_param_type = self.get_openapi_type(query_param_annotations[query_param])

                openapi_path_object["parameters"].append(
                    {
                        "name": query_param,
                        "in": "query",
                        "required": False,
                        "schema": {"type": query_param_type},
                    }
                )

        if request_body:
            if is_pydantic_model(request_body):
                schema, component_schemas = get_pydantic_openapi_schema(request_body)
                if component_schemas:
                    self._merge_component_schemas(component_schemas)
                request_body_object = {"content": {"application/json": {"schema": schema}}}
            else:
                properties = {}
                request_body_annotations = request_body.__annotations__ if request_body is TypedDict else typing.get_type_hints(request_body)
                for body_item in request_body_annotations:
                    properties[body_item] = self.get_schema_object(body_item, request_body_annotations[body_item])
                request_body_object = {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": properties,
                            }
                        }
                    }
                }

            openapi_path_object["requestBody"] = request_body_object

        response_schema: dict = {}
        response_type = "text/plain"

        if return_annotation and return_annotation is not Response:
            response_type = "application/json"
            response_schema = self.get_schema_object("response object", return_annotation)

        success_status = str(meta.status_code) if meta.status_code is not None else "200"

        openapi_path_object["responses"] = {success_status: {"description": "Successful Response", "content": {response_type: {"schema": response_schema}}}}

        # Merge any user-declared additional responses (e.g. 404, 422) so a single
        # operation can document multiple outcomes (#1257).
        if meta.responses:
            for status, response in self._build_responses(meta.responses).items():
                openapi_path_object["responses"][status] = response

        return endpoint_with_path_params_wrapped_in_braces, openapi_path_object

    def _build_responses(self, responses: dict[int | str, Any]) -> dict[str, dict]:
        """Normalise user-supplied ``responses=`` into OpenAPI Response Objects.

        Each value may be:
          - a plain ``str`` (used as the response ``description``),
          - a dict with an optional ``model`` key (a type/Pydantic model whose schema
            becomes ``content.application/json.schema``), or
          - a fully-formed OpenAPI Response Object (passed through unchanged).
        """
        built: dict[str, dict] = {}
        for status, value in responses.items():
            key = str(status)

            if isinstance(value, str):
                built[key] = {"description": value}
                continue

            if not isinstance(value, dict):
                _logger.warning("OpenAPI response for status %s is not a str or dict — ignoring", key)
                continue

            response_obj = {k: v for k, v in value.items() if k != "model"}
            response_obj.setdefault("description", "")

            model = value.get("model")
            if model is not None:
                schema = self.get_schema_object("response object", model)
                response_obj.setdefault("content", {})["application/json"] = {"schema": schema}

            built[key] = response_obj
        return built

    def get_openapi_type(self, typed_dict: str_typed_dict) -> str:
        """
        Get actual type from the TypedDict annotations

        @param typed_dict: TypedDict The TypedDict to be converted
        @return: str the type inferred
        """
        if typed_dict in _PRIMITIVE_TYPE_NAMES:
            return _PRIMITIVE_TYPE_NAMES[typed_dict]

        if typed_dict in _LEAF_TYPE_SCHEMAS:
            return _LEAF_TYPE_SCHEMAS[typed_dict]["type"]

        # default to "string" if type is not found
        return "string"

    def get_schema_object(self, parameter: str, param_type: Any) -> dict:
        """
        Get the schema object for request/response body

        @param parameter: name of the parameter
        @param param_type: Any the type to be inferred
        @return: dict the properties object
        """

        properties: dict = {
            "title": parameter.capitalize(),
        }

        # Primitive scalars (int, str, bool, float, dict, list).
        if param_type in _PRIMITIVE_TYPE_NAMES:
            properties["type"] = _PRIMITIVE_TYPE_NAMES[param_type]
            return properties

        # Special stdlib leaf types (datetime, date, UUID, Decimal, bytes, ...).
        # Pydantic-free handlers can return these without crashing or rendering
        # as a bare object (#1124).
        if isinstance(param_type, type) and param_type in _LEAF_TYPE_SCHEMAS:
            properties.update(_LEAF_TYPE_SCHEMAS[param_type])
            return properties

        # typing.Any -> any value, no constraints.
        if param_type is Any:
            return properties

        origin = get_origin(param_type)
        args = get_args(param_type)

        # typing.Literal[...] -> an enum of literal values.
        if origin is typing.Literal:
            properties["enum"] = list(args)
            inferred = type(args[0]) if args else str
            properties["type"] = _PRIMITIVE_TYPE_NAMES.get(inferred, "string")
            return properties

        # enum.Enum subclass -> enum of member values.
        if isinstance(param_type, type) and issubclass(param_type, enum.Enum):
            members = list(param_type)
            properties["enum"] = [member.value for member in members]
            if members:
                properties["type"] = _PRIMITIVE_TYPE_NAMES.get(type(members[0].value), "string")
            return properties

        # Sequence generics (list[X], tuple[X, ...], set[X]) -> array.
        if origin in (list, tuple, set, frozenset):
            properties["type"] = "array"
            if args:
                item_type = args[0]
                properties["items"] = self.get_schema_object(f"{parameter}_item", item_type)
            return properties

        # Mapping generics (dict[str, V]) -> object with typed additionalProperties.
        if origin is dict:
            properties["type"] = "object"
            if len(args) == 2:
                properties["additionalProperties"] = self.get_schema_object(f"{parameter}_value", args[1])
            return properties

        is_union = origin in (typing.Union, types.UnionType)
        if is_union and args:
            non_none_args = [a for a in args if a is not type(None)]
            nullable = type(None) in args

            any_of: list[dict] = []
            for arg in non_none_args:
                if arg in _PRIMITIVE_TYPE_NAMES:
                    any_of.append({"type": _PRIMITIVE_TYPE_NAMES[arg]})
                elif isinstance(arg, type) and arg in _LEAF_TYPE_SCHEMAS:
                    any_of.append(dict(_LEAF_TYPE_SCHEMAS[arg]))
                else:
                    any_of.append(self.get_schema_object(parameter, arg))
            if nullable:
                any_of.append({"type": "null"})

            properties["anyOf"] = any_of
            return properties

        if is_pydantic_model(param_type):
            schema, component_schemas = get_pydantic_openapi_schema(param_type)
            if component_schemas:
                self._merge_component_schemas(component_schemas)
            return schema

        # check for custom classes and TypedDicts
        if inspect.isclass(param_type):
            properties["type"] = "object"
            properties["properties"] = {}
            if hasattr(param_type, "__annotations__"):
                # get_type_hints resolves PEP 563 string annotations (e.g. "list[int]");
                # fall back to the raw __annotations__ if they can't be resolved.
                try:
                    annotations = typing.get_type_hints(param_type)
                except Exception:
                    annotations = dict(param_type.__annotations__)
                for field_name, field_type in annotations.items():
                    properties["properties"][field_name] = self.get_schema_object(field_name, field_type)
            return properties

        properties["type"] = "object"
        return properties

    def override_openapi(self, openapi_json_spec_path: Path):
        """
        Set a pre-configured OpenAPI spec
        @param openapi_json_spec_path: str the path to the json file
        """
        with open(openapi_json_spec_path) as json_file:
            json_file_content = json.load(json_file)
            self.openapi_spec = dict(json_file_content)
            self.openapi_file_override = True

    def get_openapi_docs_page(self) -> Response:
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
