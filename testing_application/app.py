from robyn import Robyn

schema = {
    "openapi": "3.0.0",
    "info": {"title": "Sample API", "version": "1.0.0"},
}

app = Robyn(__file__, schema)


@app.get("/")
async def welcome():
    return "hiiiiii"


@app.get("/users/{name}", openapi_summary="Get User by ID", openapi_tags=["Users"])
async def get_user(name: str):
    return {"message": f"User {name}"}


if __name__ == "__main__":
    app.start()
