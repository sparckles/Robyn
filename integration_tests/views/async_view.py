from robyn.robyn import Request


def AsyncView():
    async def get():
        return "Hello, world!"

    async def post(request: Request):
        body = request.body.as_str()
        return {
            "status": 200,
            "body": body,
            "headers": {"Content-Type": "text/json"},
        }
