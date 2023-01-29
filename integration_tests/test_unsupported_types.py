import pytest
import requests

BASE_URL = "http://127.0.0.1:8080"


from requests.exceptions import ConnectionError


def test_bad_body_type_error_sync(session):
    with pytest.raises(ConnectionError):
        _ = requests.get(f"{BASE_URL}/bad_body_type_error_sync")


# def test_bad_body_type_error_async(session):
#     with pytest.raises(ConnectionError):
#         _ = requests.get(f"{BASE_URL}/bad_body_type_error_async")
