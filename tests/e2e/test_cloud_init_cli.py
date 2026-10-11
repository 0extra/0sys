from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from zerosys.backends.cloudinit import CLOUD_CONFIG_HEADER
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
        "packages:\n"
        "  install: [nginx, ufw]\n"
        "firewall:\n"
        "  default: deny\n"
        "  allow: [22, 80]\n",
        encoding="utf-8",
    )
    return path


def test_cloud_init_writes_file(runner: CliRunner, config_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "user-data.yaml"

    result = runner.invoke(
        app,
        ["cloud-init", str(config_file), "-o", str(target)],
    )

    assert result.exit_code == 0
    assert target.exists()
    assert target.read_text(encoding="utf-8").startswith(CLOUD_CONFIG_HEADER)


def test_cloud_init_print_mode(runner: CliRunner, config_file: Path) -> None:
    result = runner.invoke(app, ["cloud-init", str(config_file), "--print"])

    assert result.exit_code == 0
    assert "cloud-config" in result.stdout
    assert "nginx" in result.stdout


def test_cloud_init_help_lists_command(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "cloud-init" in result.stdout
