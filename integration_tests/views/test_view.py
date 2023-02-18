from robyn import jsonify


def TestView():
    def get():
        return "Hello, world!"

    def post(request):
        body = bytes(request["body"]).decode("utf-8")
        print(body)
        return {
            "status": 200,
            "body": body,
            "headers": {"Content-Type": "text/json"},
        }
