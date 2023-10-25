import unittest
import webbrowser
import os
import shutil
from robyn.__main__ import create_robyn_app, docs


class TestCreateRobynApp(unittest.TestCase):
    def setUp(self) -> None:
        self.test_directory_name = "app1"
        self.is_docker_needed_yes = "Y"
        self.is_docker_needed_no = "N"

    def tearDown(self) -> None:
        if os.path.exists(self.test_directory_name):
            shutil.rmtree(self.test_directory_name)

    def test_directory_creation(self) -> None:
        create_robyn_app(self.test_directory_name, self.is_docker_needed_yes)
        self.assertTrue(os.path.exists(self.test_directory_name))

    def test_directory_content_creation_with_docker(self) -> None:
        create_robyn_app(self.test_directory_name, self.is_docker_needed_yes)
        app_file_path = os.path.join(self.test_directory_name, "app.py")
        docker_file_path = os.path.join(self.test_directory_name, "Dockerfile")
        self.assertTrue(os.path.exists(app_file_path))
        self.assertTrue(os.path.exists(docker_file_path))
        with open(app_file_path, "r") as app_file:
            content = app_file.read()
            self.assertTrue("from robyn import Robyn" in content)
            self.assertTrue("app = Robyn(__file__)" in content)
            self.assertTrue("app.start()" in content)
        with open(docker_file_path, "r") as docker_file:
            content = docker_file.read()
            self.assertTrue("FROM ubuntu:22.04" in content)
            self.assertTrue("RUN pip install --no-cache-dir --upgrade robyn" in content)
            self.assertTrue(
                'CMD ["python3.10", "/workspace/foo/app.py", "--log-level=DEBUG"]'
            )

    def test_directory_content_without_docker(self) -> None:
        create_robyn_app(self.test_directory_name, self.is_docker_needed_no)
        app_file_path = os.path.join(self.test_directory_name, "app.py")
        docker_file_path = os.path.join(self.test_directory_name, "Dockerfile")
        self.assertTrue(os.path.exists(app_file_path))
        self.assertFalse(os.path.exists(docker_file_path))
        with open(app_file_path, "r") as app_file:
            content = app_file.read()
            self.assertTrue("from robyn import Robyn" in content)
            self.assertTrue("app = Robyn(__file__)" in content)
            self.assertTrue("app.start()" in content)


class TestDocs(unittest.TestCase):
    def test_docs_opens_correct_url(self):
        expected_url = "https://sparckles.github.io/Robyn/#/"
        with unittest.mock.patch.object(webbrowser, "open") as mock_open:
            docs()
        mock_open.assert_called_with(expected_url)
