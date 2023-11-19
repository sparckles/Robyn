import inspect
from robyn import Robyn, Request, serve_html
import re
import json
import robyn

app = Robyn(__file__)
openapi_schema = {
    "openapi": "3.0.0",
    "info": {"title": "Sample API", "version": "1.0.0"},
    "paths": {},
}


def extract_path_params(path: str):
    return re.findall(r"{(.*?)}", path)


def openapi_route(path: str, method: str, summary: str, tags: list):
    def decorator(func):
        if path not in openapi_schema["paths"]:
            openapi_schema["paths"][path] = {}

        path_params = extract_path_params(path)
        parameters = []
        for param in path_params:
            parameters.append(
                {
                    "name": param,
                    "in": "path",
                    "required": True,
                    "schema": {
                        "type": "string"
                    },  # You might need to adjust the type based on your API design.
                }
            )

        openapi_schema["paths"][path][method.lower()] = {
            "summary": summary,
            "tags": tags,
            "parameters": parameters,
            # requestBody and responses can be added here if needed
        }
        return func

    return decorator


@app.get("/users/{user_id}")
@openapi_route("/users/{user_id}", "GET", "Get User by ID", ["Users"])
async def get_user(
    request: Request,
    user_id: str,
    query: str,
    body: robyn.Body = {
        "name": str,
        "age": int,
    }
    # for validators
):
    # Your route implementation here
    return {"message": f"User {user_id}"}


@app.get("/openapi.json")
async def openapi_json():
    return json.dumps(openapi_schema)


# Function to serve Swagger UI (requires hosting Swagger UI assets)
@app.get("/docs")
async def swagger_ui():
    import os

    cwd = os.getcwd()
    html_file = os.path.join(cwd, "swagger.html")
    print(html_file)

    return serve_html(html_file)


if __name__ == "__main__":
    app.start()
