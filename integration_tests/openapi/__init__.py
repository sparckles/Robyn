from typing import TypedDict

from robyn import Robyn, Request, jsonify, OpenAPI, SubRouter
from robyn.openapi import OpenAPIInfo, Contact, License, ExternalDocumentation, Components

pet_sample_app = Robyn(
    file_object=__file__,
    openapi=OpenAPI(
        info=OpenAPIInfo(
            title="Sample Pet Store App",
            description=" This is a sample server for a pet store.",
            termsOfService=" https://example.com/terms/",
            version=" 1.0.1",
            contact=Contact(
                name="API Support",
                url="https://www.example.com/support",
                email="support@example.com",
            ),
            license=License(
                name="Apache 2.0",
                url="https://www.apache.org/licenses/LICENSE-2.0.html",
            ),
            servers=[
                # Server(
                #     url="//",
                #     description="Debug environment"
                # ),
                # Server(
                #     url="https://example.com/api/v1/",
                #     description="Production environment"
                # ),
            ],
            externalDocs=ExternalDocumentation(description="Find more info here", url="https://example.com/"),
            components=Components(),
        ),
    ),
)


@pet_sample_app.get("/")
async def welcome():
    """hiiii"""
    return "hiiiiii"


class GetParams(TypedDict):
    appointment_id: str
    year: int


@pet_sample_app.get("/users/:name/:age", openapi_tags=["Pet"])
async def get_pet(r: Request, query_params=GetParams):
    """Get Pet by ID"""
    return jsonify(r.path_params)


@pet_sample_app.delete("/users/:name/:age", openapi_tags=["Pet"])
async def delete_pet(r: Request):
    """Delete Pet by ID"""
    return jsonify(r.path_params)


doctor_subrouter = SubRouter(__name__, prefix="/doctor")


@doctor_subrouter.get("//")
async def doctor_welcome():
    """hiiii doctor"""
    return "hiiiiii doctor"


@doctor_subrouter.get("/users/:name/:age")
async def get_doctor(r: Request):
    """Get Doctor by ID"""
    return jsonify(r.path_params)


@doctor_subrouter.delete("/users/:name/:age")
async def delete_doctor(r: Request):
    """Delete Doctor by ID"""
    return jsonify(r.path_params)


pet_sample_app.include_router(doctor_subrouter)

if __name__ == "__main__":
    pet_sample_app.start()

# query params ->> typed dict
# subrouter impl for openapi

# add_direcotry
