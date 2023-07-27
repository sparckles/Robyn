from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from functools import wraps
import inspect
from inspect import signature
from types import CoroutineType
from typing import Callable, Dict, List, NamedTuple, Union, Optional
from robyn.authentication import AuthenticationHandler, AuthenticationNotConfiguredError

from robyn.robyn import FunctionInfo, HttpMethod, MiddlewareType, Request, Response
from robyn import status_codes
from robyn.ws import WS


class Route(NamedTuple):
    route_type: HttpMethod
    route: str
    function: FunctionInfo
    is_const: bool


class RouteMiddleware(NamedTuple):
    middleware_type: MiddlewareType
    route: str
    function: FunctionInfo


class GlobalMiddleware(NamedTuple):
    middleware_type: MiddlewareType
    function: FunctionInfo


class BaseRouter(ABC):
    @abstractmethod
    def add_route(*args) -> Union[Callable, CoroutineType, WS]:
        ...


class Router(BaseRouter): #base class of app=Route(__file__) declared here
    def __init__(self) -> None:
        super().__init__()
        self.routes: List[Route] = []
        #self.dependencies = {}

    def _format_response(self, res, request=None):
        if callable(res):
            if request is not None:
                return res(request)
            else:
                return res()
        response = {}
        if isinstance(res, dict):
            status_code = res.get("status_code", status_codes.HTTP_200_OK)
            headers = res.get("headers", {"Content-Type": "text/plain"})
            body = res.get("body", "")

            if type(status_code) != int:
                status_code = int(status_code)  # status_code can potentially be string

            response = Response(status_code=status_code, headers=headers, body=body)
            file_path = res.get("file_path")
            if file_path is not None:
                response.file_path = file_path
        elif isinstance(res, Response):
            response = res
        elif isinstance(res, bytes):
            response = Response(
                status_code=status_codes.HTTP_200_OK,
                headers={"Content-Type": "application/octet-stream"},
                body=res,
            )
        else:
            response = Response(
                status_code=status_codes.HTTP_200_OK,
                headers={"Content-Type": "text/plain"},
                body=str(res).encode("utf-8"),
            )
        return response
    #certain methods like add_route and other decorators
    #return self._add_route(HttpMethod.GET, endpoint, handler, const)
    def add_route(
        self,
        route_type: HttpMethod,
        endpoint: str,
        handler: Callable, #hello world function
        is_const: bool,
        dependencies: Dict[str,any],
        exception_handler: Optional[Callable],
    ) -> Union[Callable, CoroutineType]:
        #print("router.py, add_route(), dependencies:", dependencies)
        #print("router.py, add_route, Endpoint:", endpoint)
        @wraps(handler)
        async def async_inner_handler(*args):
            signatureObj = (inspect.signature(handler))
            argsFromHandler = signatureObj.parameters.values() #holds all args from func args
            specificDep = dependencies.get(endpoint, dependencies["all"])
            depToPass = [] 
            #not_deps = ""
            for a in argsFromHandler: #for each handler func param
                #if a.name != "request" and a.name!= "response": #if not request, response
                if not any(a.name == key for key, _ in specificDep.items()): #if param was not specified in app's dep dictionary
                    raise ValueError("Required dependency,", a.name, "has not been injected for this route.")
                for key,value in specificDep.items(): 
                    if key == a.name:
                        depToPass.append(value)
            try:
                if depToPass:
                    response = self._format_response(await handler( *depToPass))#next(iter(depToPass.values()))))
                else: 
                    response = self._format_response(await handler(*args,))
            except Exception as err:
                if exception_handler is None:
                    raise
                response = self._format_response(exception_handler(err))
            return response


        @wraps(handler) 
        def inner_handler(*args):
            print("router.py,inner_handler, route:",endpoint)
            signatureObj = (inspect.signature(handler))
            argsFromHandler = signatureObj.parameters.values() #holds all args from func args
            print("router.py, inner_handler: Args from handler",(argsFromHandler))
            specificDep = dependencies.get(endpoint, dependencies["all"])
            print("router.py, inner_handler, specificDep",specificDep)
            '''if endpoint in dependencies: #if endpoint mentioned in handler is an entry in dependencies list
                print(endpoint, "is in dependencies",dependencies)
                #inSpecific = True
                specificDep = dependencies[endpoint] #specific dependency dictionary entry,need to find way to allow specified dep to use all
            else:
                print(endpoint, "not specified in dependencies", dependencies) #ex: /ssssss is written endpoint but not specf'd in deps
                #inSpecific = False
                specificDep = dependencies["all"] #dep[all] is list of dicts
                print("specificDep",specificDep)'''
            depToPass = [] 
            #not_deps = ""
            for a in argsFromHandler: #for each handler func param
                print("A",a.name)
                print("router.py, a.name",a.name, " specificDep:",specificDep)
                '''if a.name == "request" or a.name == "response":
                    not_deps = a
                    print("Not deps in fxn:", a)'''
                #if a.name != "request" and a.name!= "response": #if not request, response
                if not any(a.name == key for key, _ in specificDep.items()): #if param was not specified in app's dep dictionary
                    raise ValueError("Required dependency,", a.name, "has not been injected for this route.")
                for key,value in specificDep.items(): #compare each handler func param with each key,value pair
                    if key == a.name:
                        print("router.py, a.name",a.name, " key:",key," value:",value)
                        depToPass.append(value)
                        print("router.py, inner_handler, depToPass update:",depToPass)
                
            '''if specificDep == "not supposed to run":#!= dependencies["all"]: #if specific dep dict is not the one accessible to all
                for a in argsFromHandler:
                    print("router.py, inner handler, arg from handler",a.name, "    dependency dict:",specificDep)
                    if a.name in specificDep: #check specificDep to see if func param is there
                        #depToPass = specificDep#a.name commented after creating depToPass list
                        #print("Dep to pass was valid", depToPass)
                        depToPass.append(specificDep[a.name])
                    elif a.name not in specificDep: #check all dict
                        print("router.py, inner handler, a.name not in specDep", a.name, " specificDep:", specificDep, " Dep to pass was empty", depToPass)
                        for dep_dict in dependencies["all"]:
                            print("router.py, inner handler, dependency dict in dependencies all", dep_dict)
                            if a.name in dep_dict:
                                depToPass.append(dep_dict[a.name])
                                print("router.py, inner handler, dep to pass after checking all dict:", depToPass)
                    #if depToPass == []: # = "" #means func param not in specificDep, have to check the one accessible to all
                    print("Dep to pass was empty", depToPass)
                    for a in argsFromHandler:
                        for dep_dict in dependencies["all"]:
                            if a.name in dep_dict:
                                depToPass.append(specificDep[a.name])
                                print("Dep to pass from specified route that has to access all dict:", depToPass)
            else: #if specified dep dict is the same as the "all" dict
                for a in argsFromHandler:
                    print("router.py, inner_handler(), arg from handler",a.name, "    dependency dict being looked through:",specificDep)
                    for dep_dict in dependencies["all"]:
                        if a.name in dep_dict:
                            depToPass.append(dep_dict[a.name])
                            print("router.py, inner_handler(), Unspecified route's depToPass:",depToPass) #retrieve specific dict of the dependency listed in func args'''
                #if a.name in [i for i in specificDep if a.name in i] or a.name in [i for i in dependencies["all"] if a.name in i] :
                    #depToPass = a.name
                    #print("dep to pass", dependencies[depToPass])
            '''
            Test cases: (+)=done (-)=ToDo
            - unspecified injection: make sure accessible by any    -> /    
            - unspecified injection: make sure accessible by routes that had specified dep inject      ->      /s    
            - specified injection: make sure accessible by spec'd routes   ->    /s
            - specified injection: make sure unaccessible by any route   ->     /
            --> all work for now
            ToDo:
            * subrouters to have own set of dependencies, inherit deps from greater route. If we have dep mapped to global router.
            ... should be accessible via subrouter
            * try "app.inject_dependency("/route", HTTP.GET, dependency2)"
            * take in multiple dependency args from inject fxn
            '''
            try:
                #if depToPass: #specificDep != dependencies["all"] and inSpecific is True:#depToPass != "" and inSpecific is True:
                #    print("try block, dep specified")
                if depToPass:
                    print("router.py, args",args,"depToPass",depToPass)
                    response = self._format_response(handler( *depToPass))#next(iter(depToPass.values()))))
                else: 
                    response = self._format_response(handler(*args,))
                '''elif specificDep != dependencies["all"] and inSpecific is False:
                    response = self._format_response(handler(*args, next(iter(depToPass.values()))))
                elif specificDep == dependencies["all"]:#depToPass != "" and specific is False:
                    response = self._format_response(handler(*args, next(iter(depToPass.values()))))
                    #for dep in dependencies["all"]:
                        #if depToPass == dependencies[dep]:
                         #   response = self._format_response(handler(*args,dependencies[dep]))'''
                '''else:
                    print("try block, no dep specified")
                    response = self._format_response(handler(*args,))'''
            except Exception as err:
                if exception_handler is None:
                    raise
                response = self._format_response(exception_handler(err))
            return response
        number_of_params = len(signature(handler).parameters) #this was already defined. extracting # of params passed to rust
        #print("router.py, add_route, ran before inner_handler, Params:", signature(handler).parameters, "   NUMBER OF PARAMS",number_of_params)
        #depending on that, we are executing whatever
        '''params = signature(handler).parameters 
        for param in params:
            if param is not Request and params is not Response:
                if param not in dependencies:
                    print("dependencies: ",dependencies, ",param,", param,   "   Not in DEPENDENCIES")
                else:
                    depToInject = param
                    print('dep to inject',depToInject)    
        print("Endpoint", endpoint, '   these are params: ',params) #gives ordered dict of params'''
        '''extract num of parameters extracting to rust. we can find params 
        check if self.dependencies dictionary or "parameters that we are passing are not of the keyword request or response" '''
        #print("router.py, add_route, Dependencies from router.py",dependencies)
        if iscoroutinefunction(handler):
            function = FunctionInfo(async_inner_handler, True, number_of_params) #can have argument for functioninfo
            #parameters can get passed to get function putput. FunctionInfo used in get_function_output
            self.routes.append(Route(route_type, endpoint, function, is_const))
            return async_inner_handler
        else:
            print("router.py, inner handler, gets called upon init.py _add_route()")
            function = FunctionInfo(inner_handler, False, number_of_params) #this one gets called for our example
            self.routes.append(Route(route_type, endpoint, function, is_const))
            return inner_handler

    def get_routes(self) -> List[Route]:
        return self.routes
    

#associated with middlewares. used for @app.before_request() and @app.after_request()
class MiddlewareRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.global_middlewares: List[GlobalMiddleware] = []
        self.route_middlewares: List[RouteMiddleware] = []
        self.authentication_handler: Optional[AuthenticationHandler] = None

    def set_authentication_handler(self, authentication_handler: AuthenticationHandler):
        self.authentication_handler = authentication_handler

    def add_route(
        self, middleware_type: MiddlewareType, endpoint: str, handler: Callable
    ) -> Callable:
        number_of_params = len(signature(handler).parameters)
        function = FunctionInfo(handler, iscoroutinefunction(handler), number_of_params)
        self.route_middlewares.append(
            RouteMiddleware(middleware_type, endpoint, function)
        )
        return handler

    def add_auth_middleware(self, endpoint: str):
        """
        This method adds an authentication middleware to the specified endpoint.
        """

        def inner(handler):
            def inner_handler(request: Request, *args):
                if not self.authentication_handler:
                    raise AuthenticationNotConfiguredError()
                identity = self.authentication_handler.authenticate(request)
                if identity is None:
                    return self.authentication_handler.unauthorized_response
                request.identity = identity
                return request

            self.add_route(MiddlewareType.BEFORE_REQUEST, endpoint, inner_handler)
            return inner_handler

        return inner

    # These inner functions are basically a wrapper around the closure(decorator) being returned.
    # They take a handler, convert it into a closure and return the arguments.
    # Arguments are returned as they could be modified by the middlewares.
    def add_middleware(
        self, middleware_type: MiddlewareType, endpoint: Optional[str]
    ) -> Callable[..., None]:
        def inner(handler):
            @wraps(handler)
            async def async_inner_handler(*args):
                return await handler(*args)

            @wraps(handler)
            def inner_handler(*args):
                return handler(*args)

            if endpoint is not None:
                if iscoroutinefunction(handler):
                    self.add_route(middleware_type, endpoint, async_inner_handler)
                else:
                    self.add_route(middleware_type, endpoint, inner_handler)
            else:
                if iscoroutinefunction(handler):
                    self.global_middlewares.append(
                        GlobalMiddleware(
                            middleware_type,
                            FunctionInfo(
                                async_inner_handler,
                                True,
                                len(signature(async_inner_handler).parameters),
                            ),
                        )
                    )
                else:
                    self.global_middlewares.append(
                        GlobalMiddleware(
                            middleware_type,
                            FunctionInfo(
                                inner_handler,
                                False,
                                len(signature(inner_handler).parameters),
                            ),
                        )
                    )

        return inner

    def get_route_middlewares(self) -> List[RouteMiddleware]:
        return self.route_middlewares

    def get_global_middlewares(self) -> List[GlobalMiddleware]:
        return self.global_middlewares


class WebSocketRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = {}

    def add_route(self, endpoint: str, web_socket: WS) -> None:
        self.routes[endpoint] = web_socket

    def get_routes(self) -> Dict[str, WS]:
        return self.routes
