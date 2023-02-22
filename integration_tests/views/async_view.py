def AsyncView():
    async def get():
        return "Hello, world!"

    async def post(request):
        body = bytes(request["body"]).decode("utf-8")
        return {
            "status": 200,
            "body": body,
            "headers": {"Content-Type": "text/json"},
        }
