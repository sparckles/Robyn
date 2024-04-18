import pytest
from unittest.mock import patch
from robyn.cli import create_robyn_app, SCAFFOLD_DIR, CURRENT_WORKING_DIR


@pytest.fixture
def project_directory():
    return CURRENT_WORKING_DIR / "test_dir"


@pytest.mark.parametrize(
    "docker_input, project_type, should_remove_dockerfile",
    [
        ("N", "no-db", True),
        ("Y", "postgres", False),
        ("N", "mongo", True),
        ("Y", "sqlalchemy", False),
        ("N", "prisma", True),
        ("Y", "sqlmodel", False),
        ("N", "sqlite", True),
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
    docker_input,
    project_type,
    should_remove_dockerfile,
    project_directory,
):
    mock_prompt.return_value = {
        "directory": "test_dir",
        "docker": docker_input,
        "project_type": project_type,
    }
    create_robyn_app()
    expected_project_dir = project_directory.resolve()
    mock_makedirs.assert_called_with(expected_project_dir, exist_ok=True)
    expected_template_path = (SCAFFOLD_DIR / project_type).resolve()
    mock_copytree.assert_called_with(str(expected_template_path), str(expected_project_dir), dirs_exist_ok=True)
    dockerfile_path = expected_project_dir / "Dockerfile"
    if should_remove_dockerfile:
        mock_remove.assert_called_once_with(str(dockerfile_path))
    else:
        mock_remove.assert_not_called()
