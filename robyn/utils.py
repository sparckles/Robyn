def decode_bytearray(req):
    """
    Decodes a bytearray into a UTF-8 string
    """
    return bytearray(req["body"]).decode("utf-8")