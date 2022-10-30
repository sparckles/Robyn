import json
from typing import Any, Dict


def static_file(file_path: str) -> Dict[str, Any]:
    """
    This function will help in serving a static_file

    :param file_path str: file path to serve as a response
    """

    return {
        "type": "static_file",
        "file_path": file_path,
        # this is a hack for now
        "body": "",
        "status_code": "200",
    }


def jsonify(input_dict: dict) -> str:
    """
    This function serializes input dict to a json string

    :param input_dict dict: response of the function
    """

    return json.dumps(input_dict)
