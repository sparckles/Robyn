from typing import Optional

import requests

BASE_URL = "http://127.0.0.1:8080"


def check_response(response: requests.Response, expected_status_code: int):
    assert response.status_code == expected_status_code
    assert "global_after" in response.headers
    assert response.headers["global_after"] == "global_after_request"
    assert "server" in response.headers
    assert response.headers["server"] == "robyn"


def get(
    endpoint: str, expected_status_code: int = 200, headers: dict = {}
) -> requests.Response:
    endpoint = endpoint.strip("/")
    response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers)
    check_response(response, expected_status_code)
    return response


def post(
    endpoint: str,
    data: Optional[dict] = None,
    expected_status_code: int = 200,
    headers: dict = {},
) -> requests.Response:
    endpoint = endpoint.strip("/")
    response = requests.post(f"{BASE_URL}/{endpoint}", data=data, headers=headers)
    check_response(response, expected_status_code)
    return response


def put(
    endpoint: str,
    data: Optional[dict] = None,
    expected_status_code: int = 200,
    headers: dict = {},
) -> requests.Response:
    endpoint = endpoint.strip("/")
    response = requests.put(f"{BASE_URL}/{endpoint}", data=data, headers=headers)
    check_response(response, expected_status_code)
    return response


def patch(
    endpoint: str,
    data: Optional[dict] = None,
    expected_status_code: int = 200,
    headers: dict = {},
) -> requests.Response:
    endpoint = endpoint.strip("/")
    response = requests.patch(f"{BASE_URL}/{endpoint}", data=data, headers=headers)
    check_response(response, expected_status_code)
    return response


def delete(
    endpoint: str,
    data: Optional[dict] = None,
    expected_status_code: int = 200,
    headers: dict = {},
) -> requests.Response:
    endpoint = endpoint.strip("/")
    response = requests.delete(f"{BASE_URL}/{endpoint}", data=data, headers=headers)
    check_response(response, expected_status_code)
    return response

def head(
    endpoint: str,
    data: Optional[dict] = None,
    expected_status_code: int = 200,
    headers: dict = {},
) -> requests.Response:
    endpoint = endpoint.strip("/")
    response = requests.head(f"{BASE_URL}/{endpoint}", data=data, headers=headers)
    check_response(response, expected_status_code)
    return response

def generic_http_helper(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    expected_status_code: int = 200,
    headers: dict = {},
) -> requests.Response:
    endpoint = endpoint.strip("/")
    if method not in ["get", "post", "put", "patch", "delete", "options", "trace"]:
        raise ValueError(f"{method} method must be one of get, post, put, patch, delete")
    if method == "get":
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers)
    else:
        response = requests.request(method, f"{BASE_URL}/{endpoint}", data=data, headers=headers)
    try:
        check_response(response, expected_status_code)
    except AssertionError:
        raise AssertionError(f"response status code is {response.status_code}, expected {expected_status_code} of method {method}")
    return response

