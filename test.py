import roadrunner

# def helper():
async def h():
    print("This is the message from coroutine")
    return "h"


# print("Hello world")
s = roadrunner.Server()
s.add_route("/",h())
s.start()


