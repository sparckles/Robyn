
# the "app" parameter in the constructor refers to a Robyn application
# app.router leads to the router, and from there we can use app.router.get_routes()
# to retrieve the routes the server supports. We can search said list for methods
# to match test requests made by the server's developer

# it's important to understand the following classes, at least right now:
# Route, Request, Response

import asyncio, json
from typing import Callable, Optional, Union
from urllib3 import encode_multipart_formdata
from robyn import HttpMethod

# until we figure out a better method, I will be copying the classes over
class TestUrl:
    """
    The url object passed to the route handler.

    Attributes:
        scheme (str): The scheme of the url. e.g. http, https
        host (str): The host of the url. e.g. localhost,
        path (str): The path of the url. e.g. /user
    """

    scheme: str
    host: str
    path: str

class TestIdentity:
    claims: dict[str, str]

class TestRequest:
    """
    The request object passed to the route handler.

    Attributes:
        queries (dict[str, str]): The query parameters of the request. e.g. /user?id=123 -> {"id": "123"}
        headers (dict[str, str]): The headers of the request. e.g. {"Content-Type": "application/json"}
        params (dict[str, str]): The parameters of the request. e.g. /user/:id -> {"id": "123"}
        body (Union[str, bytes]): The body of the request. If the request is a JSON, it will be a dict.
        method (str): The method of the request. e.g. GET, POST, PUT, DELETE
        ip_addr (Optional[str]): The IP Address of the client
    """

    queries: dict[str, str]
    headers: dict[str, str]
    path_params: dict[str, str]
    body: Union[str, bytes]
    method: str
    url: TestUrl
    ip_addr: Optional[str]
    identity: Optional[TestIdentity]
    
    def __init__(self, queries = {}, headers = {}, path_params = {}, method = "GET", ip_addr = None):
        self.queries = queries
        self.headers = headers
        self.path_params = path_params
        self.method = method
        self.ip_addr = ip_addr
    

class TestClient:
    #helper function
    def get_route(self, path, method):
        routes = self.app.router.get_routes()
        r = None
        for route in routes: 
            if route.route == path and route.route_type == method:
                r = route
                break
        return r
    
    def __init__(self, app):
        self.app = app
    
    def get(self, method_path, data=None, json=None, headers=None, files=None):
        route = self.get_route(method_path, HttpMethod.GET)
        if route == None:
            return None
        req = TestRequest()
        return asyncio.run(route.function.handler(req))
    
    def post(self, method_path, data=None, json=None, headers=None, files=None):
        route = self.get_route(method_path, HttpMethod.POST)
        if route == None:
            return None
        req = TestRequest(method = "POST")
        #default headers
        req.headers["host"] = "localhost"
        req.headers["connection"] = "keep-alive"
        req.headers["user-agent"] = "robyn-testclient"
        req.headers["accept"] = "*/*"
        req.headers["accept-encoding"] = "gzip, deflate"
        #input headers
        if headers != None:
            for header in headers:
                req.headers[header] = headers[header]
        #input body
        if files != None:
            body, header = encode_multipart_formdata(files)
            req.headers["content-type"] = header
            req.body = list(body)
            req.headers["content-length"] = len(req.body)
        elif data != None:
            if type(data) == bytes:
                req.body = list(data)
            elif type(data) == dict:
                body = ""
                for element in data:
                    body = body + element + "=" + data + "&"
                body = body[:-1]
                req.body = list(body)
                req.headers["content-type"] = "application/x-www-form-urlencoded"
            elif type(data) == list:
                body = ""
                for element in data:
                    body = body + element[0] + "=" + element[1] + "&"
                body = body[:-1]
                req.body = list(body)
                req.headers["content-type"] = "application/x-www-form-urlencoded"
            req.headers["content-length"] = len(req.body)
        elif json == None:
            req.headers["content-type"] = "application/json"
            req.body = list(json.dumps(json))
            req.headers["content-length"] = len(req.body)
        #run the handler function
        response = asyncio.run(route.function.handler(req))
        #turn the output into a requests.Response object
        return response
    
    def delete(self, method_path, data=None, json=None, headers=None, files=None):
        route = self.get_route(method_path, HttpMethod.DELETE)
        if route is None:
            return None
        
        req = TestRequest(method="DELETE")
        
        # Set default headers
        req.headers["host"] = "localhost"
        req.headers["connection"] = "keep-alive"
        req.headers["user-agent"] = "robyn-testclient"
        req.headers["accept"] = "*/*"
        req.headers["accept-encoding"] = "gzip, deflate"
        
        

