import re


def extract_path_params(path: str):
    return re.findall(r"{(.*?)}", path)


def get_openapi_obj(path: str, summary: str, tags: list):
    path_params = extract_path_params(path)
    parameters = []
    for param in path_params:
        parameters.append(
            {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
        )

    return {
        "summary": summary,
        "tags": tags,
        "parameters": parameters,
    }
