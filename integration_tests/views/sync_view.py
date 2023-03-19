from robyn import Request


def SyncView():
    def get():
        return "Hello, world!"

    def post(request: Request):
        return request.body
