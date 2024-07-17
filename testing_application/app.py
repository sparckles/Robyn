from robyn import Robyn, Request

app = Robyn(
    file_object=__file__,
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
    return f"Successfully deleted {r.path_params['name']} : {r.path_params['age']}"


if __name__ == "__main__":
    app.start()
