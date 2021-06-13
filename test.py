import roadrunner
import asyncio
import time

# def helper():
async def h():
    print("This is the message from coroutine")
    return "not sleep function"

async def sleeper():
    await asyncio.sleep(5)
    return "sleep function"



s = roadrunner.Server()
s.add_route("GET", "/", h)
s.add_route("GET", "/sleep", sleeper)
s.start()


x = []
for i in range(4):
    x.append(asyncio.new_event_loop())

async def main():
    while True:
        pass

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
