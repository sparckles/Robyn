from unittest.mock import patch

from robyn import Robyn
from robyn.argument_parser import Config


def _make_app():
    return Robyn(__file__, config=Config())


def test_start_overrides_processes_and_workers():
    """processes/workers passed to start() override config and reach run_processes."""
    app = _make_app()
    with patch("robyn.run_processes") as mock_run:
        app.start(processes=4, workers=3, _check_port=False)

    assert app.config.processes == 4
    assert app.config.workers == 3
    # run_processes(host, port, ..., workers, processes, ...) -> workers at index 9, processes at index 10
    call_args = mock_run.call_args.args
    assert call_args[9] == 3
    assert call_args[10] == 4


def test_start_fast_fills_gaps_but_explicit_args_win():
    """fast supplies optimal defaults, but an explicit processes argument still wins."""
    app = _make_app()
    with patch("robyn.run_processes"), patch("robyn.os.cpu_count", return_value=4):
        app.start(fast=True, processes=2, _check_port=False)

    assert app.config.processes == 2  # explicit value wins over fast's (cpu*2+1)
    assert app.config.workers == 2  # filled in by fast
    assert app.config.log_level == "WARNING"  # filled in by fast


def test_start_log_level_override():
    """log_level passed to start() overrides the config value."""
    app = _make_app()
    with patch("robyn.run_processes"):
        app.start(log_level="WARN", _check_port=False)

    assert app.config.log_level == "WARN"


def test_start_without_overrides_leaves_config_untouched():
    """Calling start() with no server overrides keeps the existing config (backwards compatible)."""
    app = _make_app()
    app.config.processes = 1
    app.config.workers = 1
    with patch("robyn.run_processes") as mock_run:
        app.start(_check_port=False)

    assert app.config.processes == 1
    assert app.config.workers == 1
    assert mock_run.call_count == 1


# run_processes(host, port, ..., open_browser, ...) -> open_browser is positional index 13
_OPEN_BROWSER_ARG = 13


def test_open_browser_env_false_is_parsed_as_false(monkeypatch):
    """ROBYN_BROWSER_OPEN='false' must not open the browser (real boolean parsing, not bool('false'))."""
    app = _make_app()
    monkeypatch.setenv("ROBYN_BROWSER_OPEN", "false")
    with patch("robyn.run_processes") as mock_run:
        app.start(_check_port=False)

    assert mock_run.call_args.args[_OPEN_BROWSER_ARG] is False


def test_open_browser_env_true_is_parsed_as_true(monkeypatch):
    app = _make_app()
    monkeypatch.setenv("ROBYN_BROWSER_OPEN", "true")
    with patch("robyn.run_processes") as mock_run:
        app.start(_check_port=False)

    assert mock_run.call_args.args[_OPEN_BROWSER_ARG] is True


def test_open_browser_explicit_arg_overrides_env(monkeypatch):
    app = _make_app()
    monkeypatch.setenv("ROBYN_BROWSER_OPEN", "true")
    with patch("robyn.run_processes") as mock_run:
        app.start(_check_port=False, open_browser=False)

    assert mock_run.call_args.args[_OPEN_BROWSER_ARG] is False
