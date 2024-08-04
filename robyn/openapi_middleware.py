import json
from typing import List, Optional, Dict
import os
from dataclasses import dataclass, field, asdict


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
class OpenAPIMiddleware:
    app: object
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
        self._wrap_app_methods()
        self._register_openapi_routes()

    def _wrap_app_methods(self):
        original_get = self.app.get
        original_post = self.app.post
        original_put = self.app.put
        original_delete = self.app.delete
        original_patch = self.app.patch
        original_head = self.app.head
        original_options = self.app.options

        def wrapped_get(path, *args, **kwargs):
            self.add_route(path, "get")
            return original_get(path, *args, **kwargs)

        def wrapped_post(path, *args, **kwargs):
            self.add_route(path, "post")
            return original_post(path, *args, **kwargs)

        def wrapped_put(path, *args, **kwargs):
            self.add_route(path, "put")
            return original_put(path, *args, **kwargs)

        def wrapped_delete(path, *args, **kwargs):
            self.add_route(path, "delete")
            return original_delete(path, *args, **kwargs)

        def wrapped_patch(path, *args, **kwargs):
            self.add_route(path, "patch")
            return original_patch(path, *args, **kwargs)

        def wrapped_head(path, *args, **kwargs):
            self.add_route(path, "head")
            return original_head(path, *args, **kwargs)

        def wrapped_options(path, *args, **kwargs):
            self.add_route(path, "options")
            return original_options(path, *args, **kwargs)

        self.app.get = wrapped_get
        self.app.post = wrapped_post
        self.app.put = wrapped_put
        self.app.delete = wrapped_delete
        self.app.patch = wrapped_patch
        self.app.head = wrapped_head
        self.app.options = wrapped_options

    def add_route(self, path, method):
        if path not in self.openapi_spec["paths"]:
            self.openapi_spec["paths"][path] = {}
        self.openapi_spec["paths"][path][method.lower()] = {"summary": f"{method.upper()} {path}", "responses": {"200": {"description": "Successful response"}}}

    def update_info(self, **kwargs):
        """Update the OpenAPI info section."""
        for key, value in kwargs.items():
            if hasattr(self.info, key):
                setattr(self.info, key, value)
            elif key in self.info.contact.__annotations__:
                setattr(self.info.contact, key, value)
            elif key in self.info.license.__annotations__:
                setattr(self.info.license, key, value)
            elif key in self.info.components.__annotations__:
                setattr(self.info.components, key, value)
            elif self.info.servers and key in self.info.servers[0].__annotations__:
                for server in self.info.servers:
                    setattr(server, key, value)
            elif key in self.info.externalDocs.__annotations__:
                setattr(self.info.externalDocs, key, value)
        self.openapi_spec["info"] = asdict(self.info)
        self.openapi_spec["components"] = asdict(self.info.components)
        self.openapi_spec["servers"] = [asdict(server) for server in self.info.servers]
        if self.info.externalDocs.url:
            self.openapi_spec["externalDocs"] = asdict(self.info.externalDocs)

    def _register_openapi_routes(self):
        self.app.add_route("/openapi.json", self.openapi_spec_handler, methods=["GET"])
        self.app.add_route("/docs", self.swagger_ui_handler, methods=["GET"])

    async def openapi_spec_handler(self, request):
        return json.dumps(self.openapi_spec), {"Content-Type": "application/json"}

    async def swagger_ui_handler(self, request):
        with open(os.path.join(os.path.dirname(__file__), "swagger.html"), "r") as f:
            return f.read(), {"Content-Type": "text/html"}
