from robyn.testing import TestClient
from myapp import app

client = TestClient(app)

def test_index():
    response = client.get("/")
    print(response)

test_index()