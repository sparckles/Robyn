def static_file(file_path):
    """ This function will take a file path as a param and return an object
    instead of a string response
    """

    return {
        "response_type": "static_file",
        "file_path": file_path
    }

    
