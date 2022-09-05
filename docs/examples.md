## Examples of Using Robyn

Below are a few examples of real life use cases of Robyn.

### Creating a Simple HTTP Service
```python

from robyn import Robyn

app = Robyn(__file__)

@app.get("/")
async def h(request):
    return "Hello, world!"

app.start(port=5000)

```

### Serving simple HTML Files
```python

from robyn import Robyn, static_file

app = Robyn(__file__)

@app.get("/")
async def h(request):
    return static_file("./index.html")

app.start(port=5000)

```


### Interaction with a Database

It should be fairly easy to make a crud app example. Here's a minimal example using Prisma(`pip install prisma-client-py`) with Robyn.

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

app.start(port=5000)
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

from robyn import Robyn, static_file

app = Robyn(__file__)

@app.get("/")
async def h(request):
    return static_file("./index.html")

app.start(port=5000)

```

### A basic web socket chat app.
Coming Soon....

### Using Robyn to send an email
Coming Soon....
