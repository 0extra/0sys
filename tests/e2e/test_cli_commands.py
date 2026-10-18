from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from zerosys.cli.app import app
from zerosys.version import __version__

pytestmark = pytest.mark.e2e


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_help(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "plan" in result.stdout
    assert "apply" in result.stdout


def test_cli_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_no_args_shows_help(runner: CliRunner) -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Commands" in result.stdout


def test_examples_list(runner: CliRunner) -> None:
    result = runner.invoke(app, ["examples"])

    assert result.exit_code == 0
    assert "minimal" in result.stdout
    assert "web" in result.stdout
    assert "docker" in result.stdout


def test_examples_show_web(runner: CliRunner) -> None:
    result = runner.invoke(app, ["examples", "web"])

    assert result.exit_code == 0
    assert "nginx" in result.stdout


def test_examples_unknown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["examples", "unknown"])

    assert result.exit_code == 1


def test_init_with_preset_minimal(runner: CliRunner, tmp_path: Path) -> None:
    target = tmp_path / "prod.yaml"

    result = runner.invoke(
        app,
        ["init", "--preset", "minimal", "--hostname", "my-vps", "-o", str(target)],
    )

    assert result.exit_code == 0
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "my-vps" in content
    assert "version: 1" in content


def test_init_with_unknown_preset_fails(runner: CliRunner, tmp_path: Path) -> None:
    target = tmp_path / "prod.yaml"

    result = runner.invoke(app, ["init", "--preset", "nonsense", "-o", str(target)])

    assert result.exit_code == 1


def test_plan_with_valid_config(
    runner: CliRunner,
    tmp_config_path: Path,
    minimal_yaml: str,
) -> None:
    tmp_config_path.write_text(minimal_yaml, encoding="utf-8")

    result = runner.invoke(app, ["plan", str(tmp_config_path)])

    assert result.exit_code == 0
    assert "Execution plan" in result.stdout


def test_plan_with_broken_config(
    runner: CliRunner,
    tmp_config_path: Path,
) -> None:
    tmp_config_path.write_text("version: 1\nunknown: yes\n", encoding="utf-8")

    result = runner.invoke(app, ["plan", str(tmp_config_path)])

    assert result.exit_code != 0


def test_explain_with_valid_config(
    runner: CliRunner,
    tmp_config_path: Path,
    minimal_yaml: str,
) -> None:
    tmp_config_path.write_text(minimal_yaml, encoding="utf-8")

    result = runner.invoke(app, ["explain", str(tmp_config_path)])

    assert result.exit_code == 0
    assert "What this config will do" in result.stdout


def test_check_does_not_create_state(
    runner: CliRunner,
    tmp_config_path: Path,
    minimal_yaml: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_config_path.write_text(minimal_yaml, encoding="utf-8")
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    monkeypatch.setenv("XDG_DATA_HOME", str(state_dir))

    result = runner.invoke(app, ["check", str(tmp_config_path)])

    assert result.exit_code == 0
    assert list(state_dir.rglob("state.db")) == []


@pytest.mark.skipif(shutil.which("0sys") is None, reason="0sys not installed in PATH")
def test_console_script_0sys_version() -> None:
    completed = subprocess.run(
        ["0sys", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "0sys" in completed.stdout.lower()


@pytest.mark.skipif(shutil.which("0sys") is None, reason="0sys not installed in PATH")
def test_console_script_0sys_help() -> None:
    completed = subprocess.run(
        ["0sys", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "plan" in completed.stdout


@pytest.mark.skipif(shutil.which("zerosys") is None, reason="zerosys not installed in PATH")
def test_console_script_zerosys_version() -> None:
    completed = subprocess.run(
        ["zerosys", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "0sys" in completed.stdout.lower()
