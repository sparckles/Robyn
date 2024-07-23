from robyn import Robyn, Request, jsonify, OpenAPI, SubRouter

app = Robyn(
    file_object=__file__,
    openapi=OpenAPI(
        openapi_title="Sample Pet Store App",
        openapi_summary=" A pet store manager.",
        openapi_description=" This is a sample server for a pet store.",
        openapi_terms_of_service=" https://example.com/terms/",
        openapi_version=" 1.0.1",
        openapi_contact_name="API Support",
        openapi_contact_url="https://www.example.com/support",
        openapi_contact_email="support@example.com",
        openapi_license_name="Apache 2.0",
        openapi_license_url="https://www.apache.org/licenses/LICENSE-2.0.html",
        # openapi_servers=[
        #     {"url": "/", "description": "Debug environment"},
        #     {"url": "https://example.com/api/v1/", "description": "Production environment"},
        # ],
        # openapi_external_docs={
        #     "description": "Find more info here",
        #     "url": "https://example.com/"
        # }
    ),
)


@app.get("/")
async def welcome():
    """hiiii"""
    return "hiiiiii"


@app.get("/users/:name/:age", openapi_tags=["Users"])
async def get_user(r: Request):
    """Get User by ID"""
    return {"message": f"User {r.path_params['name']} : {r.path_params['age']}"}


@app.delete("/users/:name/:age", openapi_tags=["Users"])
async def delete_user(r: Request):
    """Delete User by ID"""
    return jsonify(r.path_params)


doctor_router = SubRouter(__name__, prefix="/doctor")


@doctor_router.get("/")
async def doctor_welcome():
    """hiiii"""
    return "doctor_hiiiiii"


@doctor_router.get("/users/:name/:age")
async def doctor_get_user(r: Request):
    """Get User by ID"""
    return {"message": f"doctor_User {r.path_params['name']} : {r.path_params['age']}"}


@doctor_router.delete("/users/:name/:age")
async def doctor_delete_user(r: Request):
    """Delete User by ID"""
    return f"doctor_{jsonify(r.path_params)}"


app.include_router(doctor_router)

if __name__ == "__main__":
    app.start()

# query params ->> typed dict
# subrouter impl for openapi

# add_direcotry
