from typing import Any

import orjson


def jsonify(data: dict[str, Any] | list[Any]) -> str:
    """
    This function serializes input data to a json string

    Attributes:
        data: dict or list to serialize as JSON response
    """
    output_binary = orjson.dumps(data)
    output_str = output_binary.decode("utf-8")
    return output_str
