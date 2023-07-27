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
mainApp.inject(example2=ex2) #unspecified inject
mainApp.inject("/s",example4=44) 
mainApp.inject(example3 = Example3)
print("mainApp, testing get_inj_dep function from init.py:", mainApp.get_injected_dependencies())
@mainApp.get("/")
def fx(request): 
    print("no dep")
    return "no dep specified"

@mainApp.get("/s")
def fx2(example3,example1,request,example2,example4): 
    example3.ex3_method()
    print(example1())
    print("success")
    return "worked"

@mainApp.get("/test3")
def fx3(request, example3,example1): 
    example3.ex3_method()
    print(example1())
    print("success")
    return "worked"

sub_router = SubRouter(__file__,"/sub_router") 
sub_router.inject(example2=Example3) 
sub_router.inject("/sub_router/hello",example3 = ex2) 
print("subrouter deps:",sub_router.get_injected_dependencies())

@sub_router.get("/hello")
def hello(example2,example3):
    example2.ex3_method()
    return "Hello, world"

@mainApp.get("/asyncTest")
async def h(request, example3):
    example3.ex3_method()
    return "Hello, world"



mainApp.include_router(sub_router) 
mainApp.start(port=8080, url="0.0.0.0")