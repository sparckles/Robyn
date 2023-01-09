## Examples of Using Robyn

Below are a few examples of real life use cases of Robyn.

### Creating a Simple HTTP Service

```python
from robyn import Robyn

app = Robyn(__file__)


@app.get("/")
async def h(request):
    return "Hello, world!"

app.start(port=8080)
```

### Serving simple HTML Files

```python
from robyn import Robyn, serve_html

app = Robyn(__file__)


@app.get("/")
async def h(request):
    return serve_html("./index.html")

app.start(port=8080)
```

### Serving files to download

```python
from robyn import Robyn, serve_file

app = Robyn(__file__)


@app.get("/")
async def h(request):
    return serve_file("./index.html")

app.start(port=8080)

```

### Interaction with a Database

It should be fairly easy to make a crud app example. Here's a minimal example using Prisma (`pip install prisma-client-py`) with Robyn.

```python
from robyn import Robyn
from prisma import Prisma
from prisma.models import User

app = Robyn(__file__)
prisma = Prisma(auto_register=True)


@app.startup_handler
async def startup_handler() -> None:
    await prisma.connect()


@app.shutdown_handler
async def shutdown_handler() -> None:
    if prisma.is_connected():
        await prisma.disconnect()


@app.get("/")
async def h():
    user = await User.prisma().create(
        data={
            "name": "Robert",
        },
    )
    return user.json(indent=2)

app.start(port=8080)
```

Using this Prisma Schema:

```prisma
datasource db {
  provider = "sqlite"
  url      = "file:dev.db"
}

generator py {
  provider = "prisma-client-py"
}

model User {
  id   String @id @default(cuid())
  name String
}
```

### Using Middleware

```python
@app.before_request("/")
async def hello_before_request(request):
    print(request)


@app.after_request("/")
def hello_after_request(request):
    print(request)
```

### A basic web socket chat app.

Coming Soon....

### Using Robyn to send an email

Coming Soon....
