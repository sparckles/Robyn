from robyn import Robyn


def test_static_directory():
    app = Robyn(__file__)
    app.set_static_files_directory()
