import pytest
from unittest.mock import patch
from robyn.argument_parser import Config
from robyn.cli import (
    create_robyn_app,
    SCAFFOLD_DIR,
    CURRENT_WORKING_DIR,
    docs,
    start_dev_server,
    start_app_normally,
)


@pytest.mark.parametrize(
    "input_values, expect_dockerfile_removal",
    [
        ({"directory": "test_dir", "docker": "N", "project_type": "no-db"}, True),
        ({"directory": "test_dir", "docker": "Y", "project_type": "postgres"}, False),
        ({"directory": "test_dir", "docker": "N", "project_type": "mongo"}, True),
        ({"directory": "test_dir", "docker": "Y", "project_type": "sqlalchemy"}, False),
        ({"directory": "test_dir", "docker": "N", "project_type": "prisma"}, True),
        ({"directory": "test_dir", "docker": "Y", "project_type": "sqlmodel"}, False),
        ({"directory": "test_dir", "docker": "N", "project_type": "sqlite"}, True),
    ],
)
@patch("os.makedirs")
@patch("shutil.copytree")
@patch("os.remove")
@patch("robyn.cli.prompt")
def test_create_robyn_app(
    mock_prompt,
    mock_remove,
    mock_copytree,
    mock_makedirs,
    input_values,
    expect_dockerfile_removal,
):
    mock_prompt.return_value = input_values

    create_robyn_app()

    project_dir = CURRENT_WORKING_DIR / input_values["directory"]
    mock_makedirs.assert_called_with(project_dir.resolve(), exist_ok=True)

    selected_project_template = (SCAFFOLD_DIR / input_values["project_type"]).resolve()
    mock_copytree.assert_called_with(str(selected_project_template), str(project_dir.resolve()), dirs_exist_ok=True)

    if expect_dockerfile_removal:
        mock_remove.assert_called_once_with(str(project_dir.resolve() / "Dockerfile"))
    else:
        mock_remove.assert_not_called()


def test_docs():
    with patch("webbrowser.open") as mock_open:
        docs()
        mock_open.assert_called_once_with("https://robyn.tech")
        assert mock_open.call_args[0][0] == "https://robyn.tech"


@patch("robyn.reloader.setup_reloader")
@patch("os.environ", {"IS_RELOADER_RUNNING": "True"})
def test_start_dev_server_already_running(mock_setup):
    config = Config()
    start_dev_server(config)
    mock_setup.assert_not_called()


@patch("subprocess.run")
def test_start_app_normally(mock_run):
    config = Config()
    start_app_normally(config)
    mock_run.assert_called()
