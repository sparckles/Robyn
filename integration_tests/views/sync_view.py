def SyncView():
    def get():
        return "Hello, world!"

    def post(request):
        body = request["body"].to_str()
        return {
            "status": 200,
            "body": body,
            "headers": {"Content-Type": "text/json"},
        }
