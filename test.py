import roadrunner
import asyncio

# def helper():
async def h():
    print("This is the message from coroutine")
    return "h"



print("Hello world")
s = roadrunner.Server()
s.add_route("/",h())
s.start()


x = []
for i in range(4):
    x.append(asyncio.new_event_loop())

print(x)
