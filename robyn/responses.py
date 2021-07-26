
from .robyn import Response
import json

def text(text):
    """
    [This function will help in serving raw text]

    :param text [str]: [text to reply with]
    """

    return Response(0,text)

def static_file(file_path):
    """
    [This function will help in serving a static_file]

    :param file_path [str]: [file path to serve as a response]
    """

    return Response(1,file_path)

def jsonify(input_dict):
    """
    [This function serializes input dict to a json string]

    :param input_dict [dict]: [response of the function]
    """
    return Response.newjson(0,0, input_dict)
    
