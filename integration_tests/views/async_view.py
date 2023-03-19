from robyn import Request


def AsyncView():
    async def get():
        return "Hello, world!"

    async def post(request: Request):
        return request.body
