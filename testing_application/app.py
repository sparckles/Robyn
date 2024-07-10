from robyn import Robyn

schema = {
    "openapi": "3.0.0",
    "info": {"title": "Sample API", "version": "1.0.0"},
    "paths": {},
}

app = Robyn(__file__, schema)


@app.get("/users/{user_id}", openapi_path="/users/{user_id}", openapi_method="GET", openapi_summary="Get User by ID", openapi_tags=["Users"])
async def get_user(user_id: str):
    return {"message": f"User {user_id}"}


if __name__ == "__main__":
    app.start()
