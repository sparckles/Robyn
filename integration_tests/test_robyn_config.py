import os
import shutil
import subprocess
import tempfile

import pytest

_HAS_ROBYN_CONFIG = shutil.which("robyn-config") is not None

pytestmark = pytest.mark.skipif(not _HAS_ROBYN_CONFIG, reason="robyn-config not installed")


class TestRobynConfigCLI:
    """Verify that the robyn-config CLI is accessible and functional."""

    def test_cli_help_exits_zero(self):
        """robyn-config --help should exit with code 0."""
        result = subprocess.run(
            ["robyn-config", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Usage" in result.stdout

    def test_cli_create_help(self):
        """robyn-config create --help should list available options."""
        result = subprocess.run(
            ["robyn-config", "create", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "create" in result.stdout.lower() or "Usage" in result.stdout

    def test_cli_add_help(self):
        """robyn-config add --help should list available options."""
        result = subprocess.run(
            ["robyn-config", "add", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0


class TestRobynConfigScaffolding:
    """Integration tests for project scaffolding."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for scaffolding tests."""
        tmp = tempfile.mkdtemp(prefix="robyn_config_test_")
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    @pytest.fixture
    def scaffolded_project(self):
        """Create a scaffolded project for tests that build on top of it."""
        tmp = tempfile.mkdtemp(prefix="robyn_config_scaffolded_")
        result = subprocess.run(
            ["robyn-config", "create", "testproj", tmp, "--design", "ddd", "--orm", "sqlalchemy"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Scaffolding failed: {result.stderr}"
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    @pytest.mark.parametrize("design", ["ddd", "mvc"])
    @pytest.mark.parametrize("orm", ["sqlalchemy", "tortoise"])
    def test_create_project_scaffold(self, temp_dir, design, orm):
        """robyn-config create should scaffold a valid project structure."""
        project_name = f"test_project_{design}_{orm}"

        result = subprocess.run(
            ["robyn-config", "create", project_name, temp_dir, "--design", design, "--orm", orm],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Verify essential files/directories exist in the scaffolded project
        assert os.path.isfile(os.path.join(temp_dir, "pyproject.toml")), "pyproject.toml not found"
        assert os.path.isdir(os.path.join(temp_dir, "src")), "src/ directory not found"
        assert os.path.isfile(os.path.join(temp_dir, "Makefile")), "Makefile not found"

    def test_adminpanel_scaffolding(self, scaffolded_project):
        """robyn-config adminpanel should add admin panel files to an existing project."""
        result = subprocess.run(
            ["robyn-config", "adminpanel", scaffolded_project],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Verify admin panel files were created
        adminpanel_dir = os.path.join(scaffolded_project, "src", "app", "infrastructure", "adminpanel")
        assert os.path.isdir(adminpanel_dir), "adminpanel directory not created"

    def test_adminpanel_with_custom_credentials(self, scaffolded_project):
        """robyn-config adminpanel should accept custom username and password."""
        result = subprocess.run(
            ["robyn-config", "adminpanel", scaffolded_project, "--username", "testadmin", "--password", "testpass"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        adminpanel_dir = os.path.join(scaffolded_project, "src", "app", "infrastructure", "adminpanel")
        assert os.path.isdir(adminpanel_dir), "adminpanel directory not created"

    def test_monitoring_scaffolding(self, scaffolded_project):
        """robyn-config monitoring should add monitoring pipeline to an existing project."""
        result = subprocess.run(
            ["robyn-config", "monitoring", scaffolded_project],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Verify monitoring files were created
        assert os.path.isfile(os.path.join(scaffolded_project, "docker-compose.monitoring.yml")), "docker-compose.monitoring.yml not found"

        monitoring_dir = os.path.join(scaffolded_project, "compose", "monitoring")
        assert os.path.isdir(monitoring_dir), "compose/monitoring directory not created"
        assert os.path.isdir(os.path.join(monitoring_dir, "alloy")), "alloy config not found"
        assert os.path.isdir(os.path.join(monitoring_dir, "grafana")), "grafana config not found"
