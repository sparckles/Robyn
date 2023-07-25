from robyn import Robyn, SubRouter

mainApp = Robyn(__file__)
print("mainApp's dependencies:", mainApp.dependencies )

def ex1():
    print("working ex1")
    return 999
def ex2():
    print("working ex2")
    return 667

class Example3:
    def __init__():
        '''print("Initialized")
        return "init initialized and returned"'''
    def ex3_method():
        print("working example 3 method printed")
        return "working example 3 returned"

mainApp.inject(example1=ex1) #specified inject, if you set to =ex1(), it will point to int return object
#mainApp.inject("/",example1 = ex1())
mainApp.inject(example2=ex2) #unspecified inject
mainApp.inject(example4=44) #when trying to access from subrouter, will also be 44
#need to make dependency map from mainApp accessible to sub_router
mainApp.inject("/test3",example3 = Example3)
print("MAINAPP.PY's dependencies after inject:", mainApp.dependencies )
getDepTest = mainApp.get_injected_dependencies()
print("mainApp, testing get_inj_dep function from init.py:", getDepTest)
@mainApp.get("/")
def fx(request,example4): #route not specified in dependencies dict, can still access dependencies in "all" sub-list
    a = example4
    print(type(a))
    print(a)
    return a
#instead of storing a list
@mainApp.get("/s")
def fx2(request, example1,example2): #todo: allow handler specified route to be able to still use dependencies in "all" sub-list
    a = example1() 
    print("ex2 value:",example2())
    print("Bit length:",a.bit_length(), "Imaginary:",a.imag, "  no problems")
    print("success")
    return "worked"

@mainApp.get("/test3")
def fx3(request, example3,example1): #todo: allow handler specified route to be able to still use dependencies in "all" sub-list
    #a = example3
    example3.ex3_method()
    print(example1())
    #print(a, "no problems")
    print("success")
    return "worked"
#prefix = sub_router
#what to work on: error handling
#subrouters, making the main dependencies dict available to sub_routers, "inheriting main's dependencies"
#web sockets?
#make request optional
#order isn't fixed, in dep dict, add key named request, Request object mapped to it
sub_router = SubRouter(__file__,"/sub_router") #added __file
sub_router.inject(example2=Example3) #collision here
sub_router.inject(example3 = ex2)
print("subrouter deps:",sub_router.get_injected_dependencies())
@sub_router.get("/hello")
def hello(request,example2):
    example2.ex3_method()
    print("Current deps",sub_router.dependencies)
    #print("Example4:",example4)
    #print("Example1:", example1())
    return "Hello, world"


mainApp.include_router(sub_router) #self = mainApp, router= sub_router
#subrouter deps: {'all': {'example2': <class '__main__.Example3'>}}
# main deps: {'all': {'example1': <function ex1 at 0x0000018E60EE04A0>, 'example2': <function ex2 at 0x0000018E6374A3E0>, 'example4': 44}, 
# ....'/test3': {'example3': <class '__main__.Example3'>, 'example1': <function ex1 at 0x0000018E60EE04A0>, 
#'example2': <function ex2 at 0x0000018E6374A3E0>, 'example4': 44}}
#collision bc main's deps will override sub_router's deps if they have the same name in the same route
mainApp.start(port=8080, url="0.0.0.0")

class Example:
    def thing_to_do(self):
        print("Hello")

    #return Example()

'''
when you do app.start -- init line 172, it will call the run_process
self.router.get_routes() gets all routes for a particular router
Main Router: contains all functions defined with app.get/post, corresponding to routes
so how do routes get populated to a router?:
- when you use app.get/post, they use smth like return self._add_route(HttpMethod.GET, endpoint, handler, const)
- _add_route function in init uses passed parameters 
...return self.router.add_route(route_type, endpoint, handler, is_const, self.exception_handler) 
...and self.router is defined as self.router = Router(). router class is defined in routers/ and whichever rs file is used depends on 
...paramters used in self.add_route(....)
X multple add.route in router.py. Which one is used depends on how the app was declared "app=Route(__file__)" (or could depend on http method?)
- robyn.pyi defines types that are not associated in python files. they are defined in rust. For example in robyn.pyi:
    ***SocketHeld class is found in src/types/shared_socket.rs
    *** MiddleWareType class is found in src/types/function_info.rs
    ***HttpMethod class is found in src/types/mod.rs
    *** FunctionInfo class is found in src/types/function_info.rs
    ***Url class is found in src/types/mod.rs
    ***Request class is found in src/types/request.rs
    ***Response class is found in src/types/response.rs
    ***Request class is found in src/types/request.rs
    ***Server class is found in src/types/server.rs
- how are these types important?: when you initialize your app through app.start, things like:
    self.router = Router() #self.router is declared with Router()
    self.middleware_router = MiddlewareRouter()
    self.web_socket_router = WebSocketRouter()
  ...get initialized. Where does Router come from? It comes from "robyn.router import .. Router..", specifically from rs files in src/routers
  ...so router.py. In router.py, Route class is defined. Router class  has methods for you to add and get routes. Do you not use these?
  ....What's the difference between add and get routes in this file and in the src/routers/ rs files? since they both have the add & gets
?Question: Is there a reason why these different classes are separated like this and not all just defined in one file?
- for every http Method, which uses http_router.rs, you have smth called RouteMap @ line 4. RouteMap = matching term router:
... maps [string: pyfunction] --pyfunction = rust type to shoot python object using this binding
... MatchItRouter contains type of FunctionInfo, defined in src/types/function_info.rs. FunctionInfo is a python class that contains
... a handler. pub number of params is important bc when we execute fxn, fxn will still run w/no error even if theres 0,1,or other # params
- http_routes.rs get_route gets called at various places: server.rs, at route execution line 10, execute http function used
... get route, extract certain things from get_route: path parameters, request, metadata. Call execute hhtp function
- executors.rs:script for all functions responsible for execution of handlers associated with route
- how is execute_http_called?: uses function metadata: check if fxn is async,it does some stuff, otherwise executes on main thread
- for dependency injection, some logic needed for mod.rs. in line 32, you use  match function.number_of_params 
...     0 => handler.call0(), if uses 0, call this
        1 => handler.call1((input.to_object(py),)), for 1 call this
        // this is done to accommodate any future params
        2_u8..=u8::MAX => handler.call1((input.to_object(py),)), 2 or more
...need to do smth to handler {}
...Dependency injection: 
you have robyn app
app = Robyn(__file__)
def fn():
    print("Hello World")
app.inject_dependency(fn)
@app.get("/")
def fx(request,fn):
    a = fn()
    return a
since injected in this app router, will be available for all routes
- by dependency injection, make dependencies avialable for handlers to execute. All execution handled in mod.rs match function.number_of_params
- execute_http_function responsible for all execution if corresponding to http method 
- change some rust code and python code to make dependency injection available to every route
- whats beneficial for us abt dependency injections: makes code more testable and cleaner
- dependencies available to subrouters: subrouter from different file, so we can have db cnxn in this file and make it available in subrouter
- in init.py why do we have to include dependencies mapping in run_processes?
- add dependency to run_process declaration and definition, and spawn_process definition
- in robyn, you have 7 kinds of hashmaps, 1 hashmap per http method. for each http method, you have path. correspondign to path, you have
function or handler associated with it
'''

'''
FLOW OF CONTROL
-develop big picture diagram of project, how flow of control is moves within robyn codebase
-visual tool: 
1. initial input: user has an application py file that they want to run. running an app involves using the start() method defined in 
....robyn/init.py
'''