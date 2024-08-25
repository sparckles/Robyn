from unittest.mock import MagicMock, patch

from robyn.cli import create_robyn_app, docs, run, start_app_normally, start_dev_server


# Unit tests
def test_create_robyn_app():
    with patch("robyn.cli.prompt") as mock_prompt:
        mock_prompt.return_value = {
            "directory": "test_dir",
            "docker": "N",
            "project_type": "no-db",
        }
        with patch("robyn.cli.os.makedirs") as mock_makedirs:
            with patch("robyn.cli.shutil.copytree") as mock_copytree, patch("robyn.os.remove") as _mock_remove:
                create_robyn_app()
                mock_makedirs.assert_called_once()
                mock_copytree.assert_called_once()


def test_docs():
    with patch("robyn.cli.webbrowser.open") as mock_open:
        docs()
        mock_open.assert_called_once_with("https://robyn.tech")


def test_start_dev_server():
    config = MagicMock()
    config.dev = True
    with patch("robyn.cli.setup_reloader") as mock_setup_reloader:
        start_dev_server(config, "test_file.py")
        mock_setup_reloader.assert_called_once()


def test_start_app_normally():
    config = MagicMock()
    config.dev = False
    config.parser.parse_known_args.return_value = (MagicMock(), [])
    with patch("robyn.cli.subprocess.run") as mock_run:
        start_app_normally(config)
        mock_run.assert_called_once()


# Integration tests
def test_run_create():
    with patch("robyn.cli.Config") as mock_config:
        mock_config.return_value.create = True
        with patch("robyn.cli.create_robyn_app") as mock_create:
            run()
            mock_create.assert_called_once()
