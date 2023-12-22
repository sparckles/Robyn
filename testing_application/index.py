from robyn import Robyn
from robyn.robyn import Headers, Response

app = Robyn(__file__)

@app.get('/')
def index():
    return Response(
        status_code=200,
        description='Hello World!',
        headers=Headers({'Content-Type': 'text/plain'})
    )

if __name__ == '__main__':
    app.start()
