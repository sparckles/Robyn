from robyn.upload import UploadFile


def test_upload_file_from_bytes():
    data = b"hello world"
    f = UploadFile(data, filename="test.txt")
    assert f.filename == "test.txt"
    assert f.content_type == "text/plain"
    assert f.size == 11
    assert f.read() == b"hello world"


def test_upload_file_seek_and_tell():
    data = b"abcdef"
    f = UploadFile(data, filename="data.bin")
    assert f.tell() == 0
    f.read(3)
    assert f.tell() == 3
    f.seek(0)
    assert f.read() == b"abcdef"


def test_upload_file_content_type_guess():
    f = UploadFile(b"", filename="photo.jpg")
    assert f.content_type == "image/jpeg"

    f2 = UploadFile(b"", filename="data.json")
    assert f2.content_type == "application/json"

    f3 = UploadFile(b"", filename="unknown")
    assert f3.content_type == "application/octet-stream"


def test_upload_file_explicit_content_type():
    f = UploadFile(b"", filename="file.txt", content_type="text/csv")
    assert f.content_type == "text/csv"


def test_upload_file_context_manager():
    data = b"context manager test"
    with UploadFile(data, filename="cm.txt") as f:
        content = f.read()
    assert content == data


def test_upload_file_repr():
    f = UploadFile(b"abc", filename="test.txt")
    r = repr(f)
    assert "test.txt" in r
    assert "text/plain" in r
    assert "3" in r
