import os
import sys
from unittest.mock import patch

from robyn.reloader import EventHandler


def _capture_reload_command(file_path, argv):
    """Run EventHandler.reload() with a faked sys.argv and return the relaunch command."""
    handler = EventHandler(file_path=file_path, directory_path=os.path.dirname(file_path))
    with (
        patch("robyn.reloader.subprocess.Popen") as mock_popen,
        patch("robyn.reloader.compile_rust_files", return_value=[]),
        patch("robyn.reloader.clean_rust_binaries"),
        patch.object(sys, "argv", argv),
    ):
        handler.reload()

    assert mock_popen.call_count == 1
    return mock_popen.call_args.args[0]


def test_reload_uses_absolute_path_when_run_as_module(tmp_path):
    """Issue #654: reloading must work when launched via `python -m ...`.

    The launcher token is absent from sys.argv[1:] and the file is passed as a
    relative path, so the relaunch must rely on the resolved absolute file path.
    """
    app = tmp_path / "app.py"
    app.write_text("")
    app_path = os.path.realpath(str(app))

    previous_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Simulates `python -m robyn app.py --dev` started from the app directory.
        command = _capture_reload_command(app_path, ["/usr/lib/python/robyn/__main__.py", "app.py", "--dev"])
    finally:
        os.chdir(previous_cwd)

    assert command[0] == sys.executable
    assert command[1] == app_path  # absolute path, not the typed "app.py" token
    assert "--dev" not in command
    assert "app.py" not in command  # the relative token must not survive
    assert command.count(app_path) == 1  # and must not be duplicated


def test_reload_forwards_extra_flags_and_strips_dev(tmp_path):
    """Non-file CLI flags are forwarded to the reloaded process; --dev is stripped."""
    app = tmp_path / "app.py"
    app.write_text("")
    app_path = os.path.realpath(str(app))

    command = _capture_reload_command(
        app_path,
        ["robyn", app_path, "--dev", "--processes", "4", "--log-level", "WARN"],
    )

    assert command == [sys.executable, app_path, "--processes", "4", "--log-level", "WARN"]


def test_reload_drops_only_the_first_app_token(tmp_path):
    """Only the first app-file token is stripped; a later arg resolving to the same path survives."""
    app = tmp_path / "app.py"
    app.write_text("")
    app_path = os.path.realpath(str(app))

    command = _capture_reload_command(app_path, ["robyn", app_path, "--dev", "--watch", app_path])

    assert command == [sys.executable, app_path, "--watch", app_path]
