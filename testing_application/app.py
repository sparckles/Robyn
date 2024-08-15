from typing import TypedDict

from robyn import Robyn, OpenAPI, Request, SubRouter
from robyn.openapi import OpenAPIInfo, Contact, License, ExternalDocumentation, Components

app: Robyn = Robyn(
    file_object=__file__,
    openapi=OpenAPI(
        info=OpenAPIInfo(
            title="Sample App",
            description="This is a sample server application.",
            termsOfService="https://example.com/terms/",
            version="1.2.2",
            contact=Contact(
                name="API Support",
                url="https://www.example.com/support",
                email="support@example.com",
            ),
            license=License(
                name="BSD2.0",
                url="https://opensource.org/license/bsd-2-clause",
            ),
            externalDocs=ExternalDocumentation(description="Find more info here", url="https://example.com/"),
            components=Components(),
        ),
    ),
)


@app.get("/")
async def welcome():
    """welcome endpoint"""
    return "hi"


class GetRequestParams(TypedDict):
    appointment_id: str
    year: int


@app.get("/api/v1/:name", openapi_tags=["Name"])
async def get(r: Request, query_params=GetRequestParams):
    """Get Name by ID"""
    return r.query_params


@app.delete("/users/:name", openapi_tags=["Name"])
async def delete(r: Request):
    """Delete Name by ID"""
    return r.path_params


subrouter: SubRouter = SubRouter(__name__, prefix="/sub")


@subrouter.get("/")
async def subrouter_welcome():
    """welcome subrouter"""
    return "hiiiiii subrouter"


class SubRouterGetRequestParams(TypedDict):
    _id: int
    value: str


@subrouter.get("/:name")
async def subrouter_get(r: Request, query_params=SubRouterGetRequestParams):
    """Get Name by ID"""
    return r.query_params


@subrouter.delete("/:name")
async def subrouter_delete(r: Request):
    """Delete Name by ID"""
    return r.path_params


app.include_router(subrouter)

if __name__ == "__main__":
    app.start()
