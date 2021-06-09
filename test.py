import roadrunner
import asyncio

# def helper():
async def h():
    print("This is the message from coroutine")
    return "h"



print("This is the message from python")
s = roadrunner.Server()
s.add_route("/",h)
s.start()


x = []
for i in range(4):
    x.append(asyncio.new_event_loop())

async def main():
    while True:
        pass

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
