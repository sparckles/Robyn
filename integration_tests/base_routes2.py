from robyn import Robyn

app = Robyn(__file__)

@app.get('/')
async def index(request):
    return 'Hello, World!'


@app.get('/help')
def index_sunc():
    return 'Hello, World!'

app.start()

