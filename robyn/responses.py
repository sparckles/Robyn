import json
import msgspec
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


def jsonify(input_dict: dict) -> bytes:
    """
    This function serializes input dict to a json string

    :param input_dict dict: response of the function
    """
    # Need to determine how to cache msgspec encoder globally
    # Need to figure out how to encode to string directly (without decoding from byte format)
    return msgspec.json.encode(input_dict).decode('utf-8')
