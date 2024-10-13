from typing import Optional

from robyn import Robyn, Request
from robyn.types import JSONResponse, Body

app: Robyn = Robyn(file_object=__file__)


class Initial(Body):
    is_present: bool
    letter: Optional[str]


class FullName(Body):
    first: str
    second: str
    initial: Initial


class CreateItemBody(Body):
    name: FullName
    description: str
    price: float
    tax: float


class CreateResponse(JSONResponse):
    success: bool
    items_changed: int


@app.post("/")
def create_item(request: Request, body: CreateItemBody) -> CreateResponse:
    return CreateResponse(success=True, items_changed=2)


if __name__ == "__main__":
    app.start()
