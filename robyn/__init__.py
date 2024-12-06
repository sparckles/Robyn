import os  # noqa: F401 this import needed for test_cli
from typing import List, Union

from robyn import status_codes
from robyn.argument_parser import Config
from robyn.authentication import AuthenticationHandler
from robyn.jsonify import jsonify
from robyn.reloader import compile_rust_files
from robyn.responses import html, serve_file, serve_html
from robyn.robyn import Headers, Request, Response, WebSocketConnector
from robyn.robyn_app import get_version, Robyn, SubRouter
from robyn.ws import WebSocket

__version__ = get_version()


config = Config()

if (compile_path := config.compile_rust_path) is not None:
    compile_rust_files(compile_path)
    print("Compiled rust files")


def ALLOW_CORS(app: Robyn, origins: Union[List[str], str]):
    """
    Configure CORS headers for the application.

    Args:
        app: Robyn application instance
        origins: List of allowed origins or "*" for all origins
    """
    # Handle string input for origins
    if isinstance(origins, str):
        origins = [origins]

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
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
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
    app.set_response_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
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
    "ALLOW_CORS",
    "SubRouter",
    "AuthenticationHandler",
    "Headers",
    "WebSocketConnector",
    "WebSocket",
]
