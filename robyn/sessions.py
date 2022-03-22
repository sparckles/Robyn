def redirect(request, location):
    request["headers"]["Location"] = location
    return {"status_code": "307", "body": "", "type": "text"}
