import json

def static_file(file_path):
    """
    [This function will help in serving a static_file]

    :param file_path [str]: [file path to serve as a response]
    """

    return {
        "response_type": "static_file",
        "file_path": file_path
    }

def jsonify(input_dict):
    """
    [This function serializes input dict to a json string]

    :param input_dict [dict]: [response of the function]
    """
    return json.dumps(input_dict)
    
