import roadrunner

# def helper():
async def h():
    print("This is the message from coroutine")


print("Hello world")
s = roadrunner.Server()
s.start()


