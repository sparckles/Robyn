from robyn import Robyn

app = Robyn(__file__)
app.inject(RouterDependency="Router Dependency")
app.inject_global(GLOBAL="Router Dependency")

@app.get('/')
def index(request):
    return 'Hello, World!'


if __name__ == '__main__':
    app.start()
