import unittest
from unittest.mock import patch
from robyn.__main__ import docs


class TestDocs(unittest.TestCase):
    @patch("webbrowser.open")
    def test_docs_opens_correct_url(self, mock_open) -> None:
        expected_url = "https://sparckles.github.io/Robyn/#/"
        docs()
        mock_open.assert_called_with(expected_url)
