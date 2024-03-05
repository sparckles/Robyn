from robyn.testing import TestClient
from myapp import app

client = TestClient(app)

def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Hello, Robyn!"

def test_upload():
    file_data = b"This is a test file"
    response = client.post("/upload", files={"file": ("test_file.txt", file_data)})
    assert response.status_code == 200
    assert response.json() == {"message": "File uploaded successfully"}
