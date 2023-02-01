from typing import Optional

import requests

BASE_URL = "http://127.0.0.1:8080"


def check_response(response: requests.Response, expected_status_code: int):
    assert response.status_code == expected_status_code
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
