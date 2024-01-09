from typing import Any, Dict

from robyn.robyn import Response, Headers


def html(html: str) -> Response:
    """
    This function will help in serving a simple html string

    :param html str: html to serve as a response
    """
    return Response(description=html, status_code=200, headers=Headers({"Content-Type": "text/html"}))


def serve_html(file_path: str) -> Dict[str, Any]:
    """
    This function will help in serving a single html file

    :param file_path str: file path to serve as a response
    """

    return {
        "file_path": file_path,
        "headers": {"Content-Type": "text/html"},
    }


def serve_file(file_path: str) -> Dict[str, Any]:
    """
    This function will help in serving a file

    :param file_path str: file path to serve as a response
    """

    return {
        "file_path": file_path,
        "headers": {"Content-Disposition": "attachment"},
    }
