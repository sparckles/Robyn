import orjson


def jsonify(input_dict: dict) -> str:
    """
    This function serializes input dict to a json string

    Attributes:
        input_dict dict: response of the function
    """
    output_binary = orjson.dumps(input_dict)
    output_str = output_binary.decode("utf-8")
    return output_str
