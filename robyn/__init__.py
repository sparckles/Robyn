import inspect
import logging
import os
import socket
import warnings
from abc import ABC
from collections.abc import Callable
from pathlib import Path
from typing import Any

import multiprocess as mp  # type: ignore

from robyn import status_codes
from robyn.argument_parser import Config
from robyn.authentication import AuthenticationHandler
from robyn.dependency_injection import DependencyMap
from robyn.env_populator import load_vars
from robyn.events import Events
from robyn.jsonify import jsonify
from robyn.logger import Colors, logger
from robyn.mcp import MCPApp
from robyn.openapi import OpenAPI, RouteOpenAPIMeta
from robyn.processpool import run_processes
from robyn.reloader import compile_rust_files
from robyn.responses import SSEMessage, SSEResponse, StreamingResponse, html, serve_file, serve_html
from robyn.robyn import FunctionInfo, Headers, HttpMethod, Request, Response, WebSocketConnector, get_version
from robyn.router import MiddlewareRouter, MiddlewareType, Router, WebSocketRouter
from robyn.session import Session, SessionManager
from robyn.testing import TestClient
from robyn.types import Directory, JsonBody, RequestBody, RequestMethod, RequestURL
from robyn.ws import WebSocketAdapter, WebSocketDisconnect, create_websocket_decorator

__version__ = get_version()


def _normalize_endpoint(endpoint: str | None, treat_empty_as_root: bool = False) -> str | None:
    """
    Normalize an endpoint to ensure consistent routing.

    Rules:
    - Root "/" remains unchanged
    - All other endpoints get leading slash added if missing
    - Trailing slashes are removed from all endpoints except root
    - Empty or blank strings are handled based on treat_empty_as_root flag
    - treat_empty_as_root is used for prefixes where empty/blank strings are valid

    Args:
        endpoint: The endpoint path to normalize.
        treat_empty_as_root (used for prefixes):
            If True, empty/blank strings are converted to "/" (root).
            If False, empty/blank strings return None (invalid endpoint).

    Returns:
        Normalized endpoint path or None if invalid.
    """
    if endpoint is None or (not endpoint and not treat_empty_as_root):
        return None

    # Remove trailing slashes
    endpoint = endpoint.strip().rstrip("/")

    # Handle empty result
    if not endpoint:
        return "/"

    # Add leading slash if missing
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint

    return endpoint


def _looks_like_module_reference(value: object) -> bool:
    """Heuristic to tell a legacy ``__name__``/``__file__`` argument apart from a
    modern route prefix, used only to keep the old SubRouter signature working.

    A module name (``__name__``) is ``"__main__"`` or a dotted path like
    ``"pkg.mod"``; ``__file__`` is a path to an existing ``.py`` file. A route
    prefix (``"/users"``) is neither.
    """
    if not isinstance(value, str):
        return False
    if value.startswith("/"):
        # Could be a prefix ("/users") or __file__ ("/abs/path/app.py").
        return value.endswith(".py") and os.path.isfile(value)
    return value == "__main__" or "." in value


config = Config()

if (compile_path := config.compile_rust_path) is not None:
    compile_rust_files(compile_path)
    print("Compiled rust files")


class BaseRobyn(ABC):
    """This is the python wrapper for the Robyn binaries."""

    def __init__(
        self,
        file_object: str,
        config: Config = Config(),
        openapi_file_path: str | None = None,
        openapi: OpenAPI | None = None,
        dependencies: DependencyMap = DependencyMap(),
    ) -> None:
        directory_path = os.path.dirname(os.path.abspath(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.config = config
        self.dependencies = dependencies
        self.openapi = openapi

        self.init_openapi(openapi_file_path)

        if not bool(os.environ.get("ROBYN_CLI", False)):
            # the env variables are already set when are running through the cli
            load_vars(project_root=directory_path)

        self._handle_dev_mode()

        logging.basicConfig(level=self.config.log_level)

        if self.config.log_level.lower() != "warn":
            logger.info(
                "SERVER IS RUNNING IN VERBOSE/DEBUG MODE. Set --log-level to WARN to run in production mode.",
                color=Colors.BLUE,
            )

        self.router = Router()
        self.middleware_router = MiddlewareRouter()
        self.web_socket_router = WebSocketRouter()
        self.request_headers: Headers = Headers({})
        self.response_headers: Headers = Headers({})
        self.excluded_response_headers_paths: list[str] | None = None
        self.directories: list[Directory] = []
        self.event_handlers: dict = {}
        self.exception_handler: Callable | None = None
        self.authentication_handler: AuthenticationHandler | None = None
        self.session_manager: SessionManager | None = None
        self.included_routers: list[SubRouter] = []
        self._mcp_app: MCPApp | None = None
        self._added_routes: set[str] = set()

    def init_openapi(self, openapi_file_path: str | None) -> None:
        if self.config.disable_openapi:
            return

        if self.openapi is None:
            self.openapi = OpenAPI()

        if openapi_file_path:
            self.openapi.override_openapi(Path(self.directory_path).joinpath(openapi_file_path))
        elif Path(self.directory_path).joinpath("openapi.json").exists():
            self.openapi.override_openapi(Path(self.directory_path).joinpath("openapi.json"))
        else:
            logger.debug("No OpenAPI spec file found; using auto-generated documentation only.", color=Colors.YELLOW)

    def _handle_dev_mode(self):
        cli_dev_mode = self.config.dev  # --dev
        env_dev_mode = os.getenv("ROBYN_DEV_MODE", "False").lower() == "true"  # ROBYN_DEV_MODE=True
        is_robyn = os.getenv("ROBYN_CLI", False)

        if cli_dev_mode and not is_robyn:
            raise SystemExit("Dev mode is not supported in the python wrapper. Please use the Robyn CLI. e.g. python3 -m robyn app.py --dev")

        if env_dev_mode and not is_robyn:
            logger.error("Ignoring ROBYN_DEV_MODE environment variable. Dev mode is not supported in the python wrapper.")
            raise SystemExit("Dev mode is not supported in the python wrapper. Please use the Robyn CLI. e.g. python3 -m robyn app.py")

    def add_route(
        self,
        route_type: HttpMethod | str,
        endpoint: str,
        handler: Callable,
        is_const: bool = False,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] | None = None,
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        Connect a URI to a handler

        :param route_type str: route type between GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS/TRACE
        :param endpoint str: endpoint for the route added
        :param handler function: represents the sync or async function passed as a handler for the route
        :param is_const bool: represents if the handler is a const function or not
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name str: the name (summary) of the endpoint in the openapi spec
        :param openapi_tags list[str]: tags for grouping endpoints in the openapi spec
        :param status_code int|None: default success status code (also reflected in the openapi spec)
        :param response_model Any: type/Pydantic model used as the success response schema
        :param responses dict|None: additional documented responses keyed by status code
        :param deprecated bool: marks the operation as deprecated in the openapi spec
        :param include_in_schema bool: when False the route is omitted from the openapi spec
        """
        injected_dependencies = self.dependencies.get_dependency_map(self)

        list_openapi_tags: list[str] = openapi_tags if openapi_tags else []

        openapi_metadata = RouteOpenAPIMeta(
            status_code=status_code,
            response_model=response_model,
            responses=responses,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
        )

        if isinstance(route_type, str):
            http_methods = {
                "GET": HttpMethod.GET,
                "POST": HttpMethod.POST,
                "PUT": HttpMethod.PUT,
                "DELETE": HttpMethod.DELETE,
                "PATCH": HttpMethod.PATCH,
                "HEAD": HttpMethod.HEAD,
                "OPTIONS": HttpMethod.OPTIONS,
            }
            route_type = http_methods[route_type]

        # Normalize endpoint before adding
        normalized_endpoint = _normalize_endpoint(endpoint)

        if normalized_endpoint is None:
            raise ValueError("Endpoint cannot be blank, do specify '/' for root endpoint")

        if auth_required:
            self.middleware_router.add_auth_middleware(normalized_endpoint, route_type)(handler)

        # Check if this exact route (method + normalized_endpoint) already exists
        route_key = f"{route_type}:{normalized_endpoint}"
        if route_key in self._added_routes:
            # Route already exists, raise an error
            raise ValueError(f"Route {route_type} {normalized_endpoint} already exists")

        # Add to our tracking set
        self._added_routes.add(route_key)

        add_route_response = self.router.add_route(
            route_type=route_type,
            endpoint=normalized_endpoint,
            handler=handler,
            is_const=is_const,
            auth_required=auth_required,
            openapi_name=openapi_name,
            openapi_tags=list_openapi_tags,
            exception_handler=self.exception_handler,
            injected_dependencies=injected_dependencies,
            openapi_metadata=openapi_metadata,
        )

        logger.info("Added route %s %s", route_type, normalized_endpoint)

        return add_route_response

    def inject(self, **kwargs):
        """
        Injects the dependencies for the route

        :param kwargs dict: the dependencies to be injected
        """
        self.dependencies.add_router_dependency(self, **kwargs)

    def inject_global(self, **kwargs):
        """
        Injects the dependencies for the global routes
        Ideally, this function should be a global function

        :param kwargs dict: the dependencies to be injected
        """
        self.dependencies.add_global_dependency(**kwargs)

    def before_request(self, endpoint: str | None = None) -> Callable[..., None]:
        """
        You can use the @app.before_request decorator to call a method before routing to the specified endpoint

        :param endpoint str|None: endpoint to server the route. If None, the middleware will be applied to all the routes.
        """
        return self.middleware_router.add_middleware(MiddlewareType.BEFORE_REQUEST, _normalize_endpoint(endpoint))

    def after_request(self, endpoint: str | None = None) -> Callable[..., None]:
        """
        You can use the @app.after_request decorator to call a method after routing to the specified endpoint

        :param endpoint str|None: endpoint to server the route. If None, the middleware will be applied to all the routes.
        """
        return self.middleware_router.add_middleware(MiddlewareType.AFTER_REQUEST, _normalize_endpoint(endpoint))

    def serve_directory(
        self,
        route: str,
        directory_path: str,
        index_file: str | None = None,
        show_files_listing: bool = False,
    ):
        """
        Serves a directory at the given route

        :param route str: the route at which the directory is to be served
        :param directory_path str: the path of the directory to be served
        :param index_file str|None: the index file to be served
        :param show_files_listing bool: if the files listing should be shown or not
        """
        self.directories.append(Directory(route, directory_path, show_files_listing, index_file))

    def add_request_header(self, key: str, value: str) -> None:
        self.request_headers.append(key, value)

    def add_response_header(self, key: str, value: str) -> None:
        self.response_headers.append(key, value)

    def set_request_header(self, key: str, value: str) -> None:
        self.request_headers.set(key, value)

    def set_response_header(self, key: str, value: str) -> None:
        self.response_headers.set(key, value)

    def exclude_response_headers_for(self, excluded_response_headers_paths: list[str] | None):
        """
        To exclude response headers from certain routes
        @param exclude_paths: the paths to exclude response headers from
        """
        self.excluded_response_headers_paths = excluded_response_headers_paths

    def add_web_socket(self, endpoint: str, handlers) -> None:
        self.web_socket_router.add_route(endpoint, handlers)

    def websocket(self, endpoint: str):
        """
        Modern WebSocket decorator backed by Rust channels.

        Usage:
            @app.websocket("/ws")
            async def handler(websocket):
                while True:
                    msg = await websocket.receive_text()
                    await websocket.send_text(f"Echo: {msg}")

            @handler.on_connect
            def on_connect(websocket):
                return "Welcome!"

            @handler.on_close
            def on_close(websocket):
                return "Goodbye"
        """
        return create_websocket_decorator(self)(endpoint)

    def _add_event_handler(self, event_type: Events, handler: Callable) -> None:
        logger.info("Added event %s handler", event_type)
        if event_type not in {Events.STARTUP, Events.SHUTDOWN}:
            return

        is_async = inspect.iscoroutinefunction(handler)
        self.event_handlers[event_type] = FunctionInfo(handler, is_async, 0, {}, {})

    def startup_handler(self, handler: Callable) -> None:
        self._add_event_handler(Events.STARTUP, handler)

    def shutdown_handler(self, handler: Callable) -> None:
        self._add_event_handler(Events.SHUTDOWN, handler)

    def is_port_in_use(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", port)) == 0
        except Exception:
            raise Exception(f"Invalid port number: {port}")

    def _add_openapi_routes(self, auth_required: bool = False):
        if self.config.disable_openapi:
            return

        if self.openapi is None:
            logger.error("No openAPI")
            return

        self.router.prepare_routes_openapi(self.openapi, self.included_routers)

        # Drop empty component buckets (e.g. an empty securitySchemes that would
        # otherwise make Swagger UI show an empty "Authorize" popup — #1122, #1339).
        self.openapi.prune_empty_components()

        self.add_route(
            route_type=HttpMethod.GET,
            endpoint="/openapi.json",
            handler=self.openapi.get_openapi_config,
            is_const=True,
            auth_required=auth_required,
            include_in_schema=False,
        )
        self.add_route(
            route_type=HttpMethod.GET,
            endpoint="/docs",
            handler=self.openapi.get_openapi_docs_page,
            is_const=True,
            auth_required=auth_required,
            include_in_schema=False,
        )
        self.exclude_response_headers_for(["/docs", "/openapi.json"])

    def exception(self, exception_handler: Callable):
        self.exception_handler = exception_handler

    def get(
        self,
        endpoint: str,
        const: bool = False,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["get"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.get decorator to add a route with the GET method

        :param endpoint str: endpoint for the route added
        :param const bool: represents if the handler is a const function or not
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.GET,
                endpoint,
                handler,
                const,
                auth_required,
                openapi_name,
                openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def post(
        self,
        endpoint: str,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["post"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.post decorator to add a route with POST method

        :param endpoint str: endpoint for the route added
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.POST,
                endpoint,
                handler,
                auth_required=auth_required,
                openapi_name=openapi_name,
                openapi_tags=openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def put(
        self,
        endpoint: str,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["put"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.put decorator to add a get route with PUT method

        :param endpoint str: endpoint for the route added
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.PUT,
                endpoint,
                handler,
                auth_required=auth_required,
                openapi_name=openapi_name,
                openapi_tags=openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def delete(
        self,
        endpoint: str,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["delete"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.delete decorator to add a route with DELETE method

        :param endpoint str: endpoint for the route added
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.DELETE,
                endpoint,
                handler,
                auth_required=auth_required,
                openapi_name=openapi_name,
                openapi_tags=openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def patch(
        self,
        endpoint: str,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["patch"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.patch decorator to add a route with PATCH method

        :param endpoint str: endpoint for the route added
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.PATCH,
                endpoint,
                handler,
                auth_required=auth_required,
                openapi_name=openapi_name,
                openapi_tags=openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def head(
        self,
        endpoint: str,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["head"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.head decorator to add a route with HEAD method

        :param endpoint str: endpoint for the route added
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.HEAD,
                endpoint,
                handler,
                auth_required=auth_required,
                openapi_name=openapi_name,
                openapi_tags=openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def options(
        self,
        endpoint: str,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["options"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.options decorator to add a route with OPTIONS method

        :param endpoint str: endpoint for the route added
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.OPTIONS,
                endpoint,
                handler,
                auth_required=auth_required,
                openapi_name=openapi_name,
                openapi_tags=openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def connect(
        self,
        endpoint: str,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["connect"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.connect decorator to add a route with CONNECT method

        :param endpoint str: endpoint for the route added
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.CONNECT,
                endpoint,
                handler,
                auth_required=auth_required,
                openapi_name=openapi_name,
                openapi_tags=openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def trace(
        self,
        endpoint: str,
        auth_required: bool = False,
        openapi_name: str = "",
        openapi_tags: list[str] = ["trace"],
        status_code: int | None = None,
        response_model: Any = None,
        responses: dict[int | str, Any] | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
    ):
        """
        The @app.trace decorator to add a route with TRACE method

        :param endpoint str: endpoint for the route added
        :param auth_required bool: represents if the route needs authentication or not
        :param openapi_name: str -- the name of the endpoint in the openapi spec
        :param openapi_tags: list[str] -- for grouping of endpoints in the openapi spec
        """

        def inner(handler):
            return self.add_route(
                HttpMethod.TRACE,
                endpoint,
                handler,
                auth_required=auth_required,
                openapi_name=openapi_name,
                openapi_tags=openapi_tags,
                status_code=status_code,
                response_model=response_model,
                responses=responses,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
            )

        return inner

    def include_router(self, router: "SubRouter"):
        """
        The method to include the routes from another router.
        Merge another SubRouter's routes, middlewares, websocket routes, and dependencies into this router.
        Note: This operation mutates the current router's internal collections (route list, middleware lists,
        websocket routes, and dependencies) and does not deep-copy the included router. Callers should ensure
        there are no path or name conflicts before including a router.

        :param router SubRouter: the router object to include the routes from
        """
        self.included_routers.append(router)

        # When *this* router carries its own prefix (i.e. we are a SubRouter
        # including a nested SubRouter), prepend it so prefixes accumulate down
        # the nesting chain (#865, #1394). HTTP routes and their route
        # middlewares already carry the included router's own prefix (applied at
        # definition time), so here we only stack *our* prefix on top of them.
        # WebSocket routes (handled below) carry no prefix yet, so they instead
        # take the included router's own prefix.
        parent_prefix = _normalize_endpoint(getattr(self, "prefix", ""), treat_empty_as_root=True)
        if parent_prefix == "/":
            parent_prefix = ""

        # Router-level tags (#554 modern syntax) are applied to every route the
        # included router contributes, accumulating through nested includes.
        included_tags = getattr(router, "tags", None) or []
        for route in router.router.routes:
            new_route = f"{parent_prefix}{route.route}"
            if included_tags:
                merged_tags = list(included_tags) + [tag for tag in route.openapi_tags if tag not in included_tags]
                self.router.routes.append(route._replace(route=new_route, openapi_tags=merged_tags))
            else:
                self.router.routes.append(route._replace(route=new_route))

        self.middleware_router.global_middlewares.extend(router.middleware_router.global_middlewares)
        for route_middleware in router.middleware_router.route_middlewares:
            self.middleware_router.route_middlewares.append(route_middleware._replace(route=f"{parent_prefix}{route_middleware.route}"))

        if not self.config.disable_openapi and self.openapi is not None:
            self.openapi.add_subrouter_paths(self.openapi)

        # extend the websocket routes
        prefix = _normalize_endpoint(router.prefix, treat_empty_as_root=True)
        if prefix == "/":
            prefix = ""
        for route, handlers in router.web_socket_router.routes.items():
            normalized_route = _normalize_endpoint(route)
            new_endpoint = f"{prefix}{normalized_route}"
            self.web_socket_router.routes[new_endpoint] = handlers

        self.dependencies.merge_dependencies(router)

        # Let the freshly-included SubRouter (and its nested SubRouters) inherit
        # an authentication handler if they don't have their own (#1026), so
        # auth_required routes on them work without a per-SubRouter
        # configure_authentication() call.
        self._propagate_authentication_handler()

    def _propagate_authentication_handler(self) -> None:
        """Share this router's authentication handler with included SubRouters
        that don't have their own, recursing into nested SubRouters.

        A SubRouter that configured its own handler keeps it (and passes *that*
        one down to its descendants); SubRouters without a handler inherit the
        nearest ancestor's. Idempotent, so it's safe to call from both
        ``configure_authentication`` and ``include_router`` regardless of order.
        """
        for router in self.included_routers:
            if router.authentication_handler is None and self.authentication_handler is not None:
                router.authentication_handler = self.authentication_handler
                router.middleware_router.set_authentication_handler(self.authentication_handler)
            router._propagate_authentication_handler()

    def configure_authentication(self, authentication_handler: AuthenticationHandler):
        """
        Configures the authentication handler for the application.

        :param authentication_handler: the instance of a class inheriting the AuthenticationHandler base class
        """
        self.authentication_handler = authentication_handler
        self.middleware_router.set_authentication_handler(authentication_handler)

        # Propagate to any already-included SubRouters lacking their own handler.
        self._propagate_authentication_handler()

        # Auto-register a matching OpenAPI security scheme so Swagger UI's
        # "Authorize" button works out of the box for auth_required routes
        # (#1122, #1339). Users can still add/override schemes via OpenAPIInfo.
        if self.openapi is not None and not self.openapi.openapi_file_override:
            token_getter = getattr(authentication_handler, "token_getter", None)
            scheme = getattr(token_getter, "scheme", "") or ""
            if scheme.lower().startswith("bearer"):
                self.openapi.add_security_scheme("BearerAuth", {"type": "http", "scheme": "bearer"})
            elif not self.openapi._security_scheme_names:
                # Generic fallback: advertise the Authorization header as an API key.
                self.openapi.add_security_scheme(
                    "ApiKeyAuth",
                    {"type": "apiKey", "in": "header", "name": "Authorization"},
                )

    def configure_sessions(
        self,
        secret_key: str,
        *,
        cookie_name: str = "session",
        max_age: int | None = 14 * 24 * 60 * 60,
        path: str = "/",
        domain: str | None = None,
        secure: bool = False,
        http_only: bool = True,
        same_site: str = "Lax",
    ) -> SessionManager:
        """
        Enable signed-cookie sessions for the application.

        Registers global ``before_request`` / ``after_request`` middleware that
        load the session from the incoming cookie and write it back to the
        response (only when the session was modified). Inside any handler, read
        or write the session via ``request.session`` (a dict-like
        :class:`Session`).

        The session is stored client-side in a tamper-proof signed cookie, so no
        server-side store is needed. The payload is signed, not encrypted — do
        not store secrets in it.

        :param secret_key: key used to sign the session cookie. Keep it secret and stable across restarts.
        :param cookie_name: name of the session cookie (default ``"session"``).
        :param max_age: session lifetime in seconds, also used as the cookie ``Max-Age``. ``None`` for a browser-session cookie.
        :param path: cookie ``Path`` attribute.
        :param domain: cookie ``Domain`` attribute.
        :param secure: only send the cookie over HTTPS.
        :param http_only: hide the cookie from JavaScript (recommended).
        :param same_site: ``"Strict"``, ``"Lax"`` or ``"None"``.
        :returns: the configured :class:`SessionManager`.
        :raises RuntimeError: if sessions are already configured on this app.
        """
        if self.session_manager is not None:
            raise RuntimeError(
                "Sessions are already configured on this app; configure_sessions() may only be called once "
                "(calling it again would register duplicate session middleware)."
            )

        manager = SessionManager(
            secret_key,
            cookie_name=cookie_name,
            max_age=max_age,
            path=path,
            domain=domain,
            secure=secure,
            http_only=http_only,
            same_site=same_site,
        )
        self.session_manager = manager

        @self.before_request()
        def _robyn_load_session(request: Request):
            # request.session is shared by reference through the request phases,
            # so handler mutations are visible when we save it below.
            request.session = manager.load(request)
            return request

        @self.after_request()
        def _robyn_save_session(request: Request, response: Response):
            session = request.session
            if session is not None:
                manager.save(session, response)
            return response

        return manager

    @property
    def mcp(self):
        """
        Get the MCP (Model Context Protocol) interface for this app.

        Enables registering MCP resources, tools, and prompts that can be accessed
        by MCP clients like Claude Desktop or other AI applications.

        Returns:
            MCPApp: MCP interface for registering handlers

        Example:
            @app.mcp.resource("file://documents", "Documents", "Access to document files")
            def get_documents(params):
                return "Document content here"

            @app.mcp.tool("calculate", "Perform calculations", {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate"}
                },
                "required": ["expression"]
            })
            def calculate_tool(args):
                return eval(args["expression"])
        """
        if self._mcp_app is None:
            self._mcp_app = MCPApp(self)
        return self._mcp_app


class Robyn(BaseRobyn):
    def start(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        _check_port: bool = True,
        client_timeout: int = 30,
        keep_alive_timeout: int = 20,
    ):
        """
        Starts the server

        :param host str: represents the host at which the server is listening
        :param port int: represents the port number at which the server is listening
        :param _check_port bool: represents if the port should be checked if it is already in use
        :param client_timeout int: timeout for client connections in seconds (default: 30)
        :param keep_alive_timeout int: timeout for keep-alive connections in seconds (default: 20)
        """

        host = os.getenv("ROBYN_HOST", host)
        port = int(os.getenv("ROBYN_PORT", port))
        client_timeout = int(os.getenv("ROBYN_CLIENT_TIMEOUT", client_timeout))
        keep_alive_timeout = int(os.getenv("ROBYN_KEEP_ALIVE_TIMEOUT", keep_alive_timeout))
        open_browser = bool(os.getenv("ROBYN_BROWSER_OPEN", self.config.open_browser))

        if _check_port:
            while self.is_port_in_use(port):
                logger.error("Port %s is already in use. Please use a different port.", port)
                try:
                    port = int(input("Enter a different port: "))
                except Exception:
                    logger.error("Invalid port number. Please enter a valid port number.")
                    continue

        if not self.config.disable_openapi:
            self._add_openapi_routes()
            logger.info("Docs hosted at http://%s:%s/docs", host, port)

        logger.info("Robyn version: %s", __version__)
        logger.info("Starting server at http://%s:%s", host, port)

        allow_connection_pickling = getattr(mp, "allow_connection_pickling", None)
        if callable(allow_connection_pickling):
            allow_connection_pickling()

        run_processes(
            host,
            port,
            self.directories,
            self.request_headers,
            self.router.get_routes(),
            self.middleware_router.get_global_middlewares(),
            self.middleware_router.get_route_middlewares(),
            self.web_socket_router.get_routes(),
            self.event_handlers,
            self.config.workers,
            self.config.processes,
            self.response_headers,
            self.excluded_response_headers_paths,
            open_browser,
            client_timeout,
            keep_alive_timeout,
        )


class SubRouter(BaseRobyn):
    """A group of routes mounted under a shared prefix.

    Modern usage (no module name required):

        users = SubRouter(prefix="/users", tags=["users"])

        @users.get("/")
        def list_users(): ...

        app.include_router(users)

    ``prefix`` may also be passed positionally (``SubRouter("/users")``), and
    ``tags`` are applied to every route the SubRouter contributes to the OpenAPI
    spec. The legacy ``SubRouter(__name__, prefix=...)`` form still works but is
    deprecated — the module argument is no longer needed and is ignored.
    """

    def __init__(
        self,
        *args,
        prefix: str = "",
        tags: list[str] | None = None,
        config: Config = Config(),
        openapi: OpenAPI = OpenAPI(),
        file_object: str | None = None,
    ) -> None:
        # `prefix` is the only argument the modern API needs and may be passed
        # positionally (``SubRouter("/users")``) or by keyword
        # (``SubRouter(prefix="/users")``).
        #
        # Back-compat: the original signature took the module name or __file__ as
        # the first positional argument. We accept *args first (rather than a
        # named `prefix`) so that ``SubRouter(__name__, prefix="/x")`` doesn't
        # raise "multiple values for argument 'prefix'". The module reference is
        # no longer needed; detect the legacy shapes, ignore it and warn.
        legacy = file_object is not None
        if args:
            if prefix:
                # prefix arrived by keyword, so a positional is the legacy module
                # reference: SubRouter(__name__, prefix="/x")
                file_object = args[0]
                legacy = True
            elif len(args) >= 2:
                # fully positional legacy form: SubRouter(__file__, "/x")
                file_object, prefix = args[0], args[1]
                legacy = True
            elif _looks_like_module_reference(args[0]):
                # lone legacy positional with no prefix: SubRouter(__name__)
                file_object = args[0]
                legacy = True
            else:
                # modern positional prefix: SubRouter("/users")
                prefix = args[0]

        if legacy:
            warnings.warn(
                "Passing a module name/__file__ to SubRouter is deprecated and ignored. Use SubRouter(prefix=...) instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        super().__init__(file_object=file_object or "", config=config, openapi=openapi)
        self.prefix = prefix
        self.tags: list[str] = list(tags) if tags else []

    def add_route(self, route_type: HttpMethod | str, endpoint: str, handler: Callable, *args, **kwargs):  # type: ignore[override]
        """
        Register a route on the subrouter, applying the subrouter prefix.

        This mirrors the decorator methods (get/post/...) so that calling
        add_route() directly on a SubRouter is not surprising (#1256).
        """
        return super().add_route(route_type, self.__add_prefix(endpoint), handler, *args, **kwargs)

    def __add_prefix(self, endpoint: str):
        # Normalize prefix, treating empty as empty (not root)
        normalized_prefix = _normalize_endpoint(self.prefix, treat_empty_as_root=True)

        # Handle empty endpoint - should just be the prefix
        if endpoint in ("", "/"):
            return normalized_prefix if normalized_prefix else "/"

        # Convert root prefix to empty to avoid double slashes when making endpoint
        if normalized_prefix == "/":
            normalized_prefix = ""  # Empty prefix for root

        # Normalize and validate endpoint
        normalized_endpoint = _normalize_endpoint(endpoint)
        if normalized_endpoint is None:
            raise ValueError("Endpoint cannot be blank, do specify '/' for root endpoint")

        return f"{normalized_prefix}{normalized_endpoint}"


def ALLOW_CORS(app: Robyn, origins: list[str] | str, headers: list[str] | str | None = None):
    """
    Configure CORS headers for the application.

    Args:
        app: Robyn application instance
        origins: List of allowed origins or "*" for all origins
        headers: List of allowed headers or "*" for all headers
    """
    # Handle string input for origins
    if isinstance(origins, str):
        origins = [origins]

    default_headers = ["Content-Type", "Authorization"]
    if isinstance(headers, list):
        headers = list(set(default_headers + headers))
        headers = ", ".join(headers)

    @app.before_request()
    def cors_middleware(request):
        origin = request.headers.get("Origin")

        # If specific origins are set, validate the request origin
        if origin and "*" not in origins and origin not in origins:
            return Response(status_code=403, description="", headers={})

        # Handle preflight requests
        if request.method == "OPTIONS":
            return Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": origin if origin else (origins[0] if origins else "*"),
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS",
                    "Access-Control-Allow-Headers": str(headers) if headers else "Content-Type, Authorization",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                },
                description="",
            )

        return request

    # Set default CORS headers for all responses
    if len(origins) == 1:
        app.set_response_header("Access-Control-Allow-Origin", origins[0])
    else:
        # For multiple origins, we'll handle it dynamically in the response
        app.set_response_header("Access-Control-Allow-Origin", "*")

    app.set_response_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS")
    app.set_response_header("Access-Control-Allow-Headers", str(headers) if headers else "Content-Type, Authorization")
    app.set_response_header("Access-Control-Allow-Credentials", "true")


__all__ = [
    "Robyn",
    "Request",
    "Response",
    "status_codes",
    "jsonify",
    "serve_file",
    "serve_html",
    "html",
    "StreamingResponse",
    "SSEResponse",
    "SSEMessage",
    "ALLOW_CORS",
    "SubRouter",
    "AuthenticationHandler",
    "Headers",
    "WebSocketConnector",
    "WebSocketAdapter",
    "WebSocketDisconnect",
    "JsonBody",
    "MCPApp",
    "TestClient",
    "RequestMethod",
    "RequestBody",
    "RequestURL",
    "Session",
    "SessionManager",
]
