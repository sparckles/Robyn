from unittest.mock import patch
from robyn.argument_parser import Config
from robyn.cli import start_app_normally


@patch("subprocess.run")
def test_start_app_normally(mock_run):
    config = Config()
    start_app_normally(config)
    mock_run.assert_called()
