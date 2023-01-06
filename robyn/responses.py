import json
from typing import Any, Dict


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


def jsonify(input_dict: dict) -> str:
    """
    This function serializes input dict to a json string

    :param input_dict dict: response of the function
    """

    return json.dumps(input_dict)
