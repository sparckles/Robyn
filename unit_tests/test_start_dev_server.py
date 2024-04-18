from unittest.mock import patch
from robyn.argument_parser import Config
from robyn.cli import start_dev_server


@patch("robyn.reloader.setup_reloader")
@patch("os.environ", {"IS_RELOADER_RUNNING": "True"})
def test_start_dev_server_already_running(mock_setup):
    config = Config()
    start_dev_server(config)
    mock_setup.assert_not_called()
