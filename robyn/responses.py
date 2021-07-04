import json

def static_file(file_path):
    """ This function will take a file path as a param and return an object
    instead of a string response.
    """

    return {
        "response_type": "static_file",
        "file_path": file_path
    }

def jsonify(input_dict):
    """ This function serializes an object in a json string.
    """
    return json.dumps(input_dict)


    
