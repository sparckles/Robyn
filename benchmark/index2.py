from sanic import Sanic
from sanic.response import text

app = Sanic("MyHelloworldapp")

@app.route('/')
async def test(request):
    return text("helloworld")

if __name__ == '__main__':
    app.run(access_log=False, fast=True)
