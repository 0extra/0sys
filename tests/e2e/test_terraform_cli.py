from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from zerosys.cli.app import app

pytestmark = pytest.mark.e2e


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "0sys.yaml"
    path.write_text(
        "version: 1\n"
        "server:\n"
        "  hostname: test-vps\n"
        "infrastructure:\n"
        "  provider: hetzner\n"
        "  region: nbg1\n"
        "  server_type: cx22\n"
        "  ssh_keys: [my-key]\n",
        encoding="utf-8",
    )
    return path


def test_terraform_writes_files(runner: CliRunner, config_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "tf"

    result = runner.invoke(
        app,
        ["terraform", str(config_file), "-o", str(target)],
    )

    assert result.exit_code == 0
    assert (target / "main.tf").exists()
    assert (target / "variables.tf").exists()
    assert (target / "outputs.tf").exists()


def test_terraform_without_infrastructure_fails(runner: CliRunner, tmp_path: Path) -> None:
    path = tmp_path / "0sys.yaml"
    path.write_text("version: 1\nserver:\n  hostname: x\n", encoding="utf-8")
    target = tmp_path / "tf"

    result = runner.invoke(
        app,
        ["terraform", str(path), "-o", str(target)],
    )

    assert result.exit_code == 1


def test_terraform_help_lists_command(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "terraform" in result.stdout
