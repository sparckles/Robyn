from robyn.robyn import Request


def SyncView():
    def get():
        return "Hello, world!"

    def post(request: Request):
        body = request.body.content
        return {
            "status": 200,
            "body": body,
            "headers": {"Content-Type": "text/json"},
        }
