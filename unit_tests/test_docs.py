from unittest.mock import patch
from robyn.cli import docs


def test_docs():
    with patch("webbrowser.open") as mock_open:
        docs()
        mock_open.assert_called_once_with("https://robyn.tech")
        assert mock_open.call_args[0][0] == "https://robyn.tech"
