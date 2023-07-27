from robyn import Robyn, SubRouter, jsonify
import json

mainApp = Robyn(__file__)

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

mainApp.inject("/s",example1=ex1) #specified inject, if you set to =ex1(), it will point to int return object
#mainApp.inject("/",example1 = ex1())
mainApp.inject(example2=ex2) #unspecified inject
mainApp.inject("/s",example4=44) #when trying to access from subrouter, will also be 44
#need to make dependency map from mainApp accessible to sub_router
mainApp.inject(example3 = Example3)
print("mainApp, testing get_inj_dep function from init.py:", mainApp.get_injected_dependencies())
@mainApp.get("/")
def fx(request): #route not specified in dependencies dict, can still access dependencies in "all" sub-list
    #a = example4
    #print(type(a))
    #print(a)
    #return a
    print("no dep")
    return "no dep specified"
#instead of storing a list
@mainApp.get("/s")
def fx2(example3,example1,request,example2,example4): #todo: allow handler specified route to be able to still use dependencies in "all" sub-list
    #a = example1() 
    #print("ex2 value:",example2())
    #print("Bit length:",a.bit_length(), "Imaginary:",a.imag, "  no problems")
    example3.ex3_method()
    print(example1())
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
sub_router.inject("/sub_router/hello",example3 = ex2) #INJECT TO SPECIFIC ROUTE?????
print("subrouter deps:",sub_router.get_injected_dependencies())
@sub_router.get("/hello")
def hello(example2,example3):
    example2.ex3_method()
    print("Current deps",sub_router.dependencies)
    #print("Example4:",example4)
    #print("Example1:", example1())
    return "Hello, world"

@mainApp.get("/asyncTest")
async def h(request, example3):
    example3.ex3_method()
    return "Hello, world"

#DB_URL = "sqlite:///./gotham_crimeData.db"
#engine = create_engine(DB_URL)



mainApp.include_router(sub_router) #self = mainApp, router= sub_router
#subrouter deps: {'all': {'example2': <class '__main__.Example3'>}}
# main deps: {'all': {'example1': <function ex1 at 0x0000018E60EE04A0>, 'example2': <function ex2 at 0x0000018E6374A3E0>, 'example4': 44}, 
# ....'/test3': {'example3': <class '__main__.Example3'>, 'example1': <function ex1 at 0x0000018E60EE04A0>, 
#'example2': <function ex2 at 0x0000018E6374A3E0>, 'example4': 44}}
#collision bc main's deps will override sub_router's deps if they have the same name in the same route
mainApp.start(port=8080, url="0.0.0.0")