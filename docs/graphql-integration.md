## GraphQl Support (<a target="_blank" href="https://strawberry.rocks/">with Strawberry 🍓</a>)

<i>This is in a very early stage right now. We will have a much more stable version when we have a stable API for Views and View Controllers.</i>

### Step 1: Creating a virtualenv

To ensure that there are isolated dependencies, we will use virtual environments.

```bash
python3 -m venv venv
```

### Step 2: Activate the virtualenv and install Robyn

#### Activating the virtualenv

```bash
source venv/bin/activate
```

#### Installing Robyn and Strawberry

```bash
pip install robyn strawberry-graphql
```

### Step 3: Coding the App

```python
from typing import List, Optional
from robyn import Robyn, jsonify
import json

import dataclasses
import strawberry
import strawberry.utils.graphiql


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> Optional[User]:
        return User(name="Hello")


schema = strawberry.Schema(Query)

app = Robyn(__file__)


@app.get("/", const=True)
async def get():
    return strawberry.utils.graphiql.get_graphiql_html()


@app.post("/")
async def post(request):
    body = json.loads(bytearray(request["body"]).decode("utf-8"))
    query = body["query"]
    variables = body.get("variables", None)
    context_value = {"request": request}
    root_value = body.get("root_value", None)
    operation_name = body.get("operation_name", None)

    data = await schema.execute(
        query,
        variables,
        context_value,
        root_value,
        operation_name,
    )

    return jsonify(
        {
            "data": (data.data),
            **({"errors": data.errors} if data.errors else {}),
            **({"extensions": data.extensions} if data.extensions else {}),
        }
    )


if __name__ == "__main__":
    app.start()
```

Let us try to decipher the usage line by line.

```python
from typing import List, Optional

from robyn import Robyn, jsonify
import json

import dataclasses
import strawberry
import strawberry.utils.graphiql
```

These statements just import the dependencies.

```python
@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> Optional[User]:
        return User(name="Hello")


schema = strawberry.Schema(Query)
```

Here, we are creating a base `User` type with a `name` property.

We are then creating a GraphQl `Query` that returns the `User`.

```python
app = Robyn(__file__)
```

Now, we are initializing a Robyn app. For us, to serve a GraphQl app, we need to have a `get` route to return the `GraphiQL`(ide) and then a post route to process the `GraphQl` request.

```python
@app.get("/", const=True)
async def get():
    return strawberry.utils.graphiql.get_graphiql_html()
```

We are populating the html page with the GraphiQL IDE using `strawberry`. We are using `const=True` to precompute this population. Essentially, making it very fast and bypassing the execution overhead in this get request.

```python
@app.post("/")
async def post(request):
    body = json.loads(bytearray(request["body"]).decode("utf-8"))
    query = body["query"]
    variables = body.get("variables", None)
    context_value = {"request": request}
    root_value = body.get("root_value", None)
    operation_name = body.get("operation_name", None)

    data = await schema.execute(
        query,
        variables,
        context_value,
        root_value,
        operation_name,
    )

    return jsonify(
        {
            "data": (data.data),
            **({"errors": data.errors} if data.errors else {}),
            **({"extensions": data.extensions} if data.extensions else {}),
        }
    )
```

Finally, we are getting params(body, query, variables, context_value, root_value, operation_name) from the `request` object.

The above is the example for just one route. You can do the same for as many as you like. :)

That's all folks. :D
