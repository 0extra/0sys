from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from zerosys.cli.app import app
from zerosys.core.planner.task import TaskKind, TaskStatus
from zerosys.core.state import StateStore
from zerosys.core.state.models import RunRecord, TaskRecord

pytestmark = pytest.mark.e2e


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def state_with_proxy(tmp_path: Path) -> Path:
    db_path = tmp_path / "state.db"
    store = StateStore(db_path)
    store.connect()
    record = RunRecord(target_host="1.2.3.4", total_tasks=1)
    store.save_run(record)
    store.save_task(
        TaskRecord(
            run_id=record.id,
            task_id="t1",
            kind=TaskKind.PROXY,
            name="configure_proxy",
            backend="ansible",
            status=TaskStatus.SUCCESS,
            params={
                "port": 9443,
                "sni": "example.com",
                "max_connections": 2048,
                "log_level": "debug",
                "version": "0.1.6",
            },
        )
    )
    store.close()
    return db_path


def test_proxy_server_info(runner: CliRunner, state_with_proxy: Path) -> None:
    result = runner.invoke(
        app,
        ["0tpe", "server-info", "--state-path", str(state_with_proxy)],
    )

    assert result.exit_code == 0
    assert "1.2.3.4" in result.stdout
    assert "9443" in result.stdout
    assert "example.com" in result.stdout
    assert "2048" in result.stdout


def test_proxy_server_info_without_state(runner: CliRunner, tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"

    result = runner.invoke(
        app,
        ["0tpe", "server-info", "--state-path", str(db_path)],
    )

    assert result.exit_code == 1


def test_proxy_client_config_explicit(runner: CliRunner, tmp_path: Path) -> None:
    target = tmp_path / "client.conf"

    result = runner.invoke(
        app,
        [
            "0tpe",
            "client-config",
            "--host",
            "1.2.3.4",
            "--port",
            "8443",
            "--sni",
            "www.microsoft.com",
            "--token",
            "deadbeef",
            "-o",
            str(target),
        ],
    )

    assert result.exit_code == 0
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "server_ip        = 1.2.3.4" in content
    assert "server_port      = 8443" in content
    assert "token            = deadbeef" in content


def test_proxy_client_config_from_state(
    runner: CliRunner, state_with_proxy: Path, tmp_path: Path
) -> None:
    target = tmp_path / "client.conf"

    result = runner.invoke(
        app,
        [
            "0tpe",
            "client-config",
            "--state-path",
            str(state_with_proxy),
            "-o",
            str(target),
        ],
    )

    assert result.exit_code == 0
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "1.2.3.4" in content
    assert "9443" in content
    assert "example.com" in content


def test_proxy_client_config_missing_args(runner: CliRunner) -> None:
    result = runner.invoke(app, ["0tpe", "client-config"])

    assert result.exit_code == 1


def test_proxy_show_config_reads_state_params(runner: CliRunner, state_with_proxy: Path) -> None:
    result = runner.invoke(
        app,
        ["0tpe", "show-config", "--state-path", str(state_with_proxy)],
    )

    assert result.exit_code == 0
    assert "listen_port     = 9443" in result.stdout
    assert "max_connections = 2048" in result.stdout
    assert "fallback_sni    = example.com" in result.stdout
    assert "log_level = debug" in result.stdout


def test_proxy_show_config_without_state(runner: CliRunner, tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"

    result = runner.invoke(
        app,
        ["0tpe", "show-config", "--state-path", str(db_path)],
    )

    assert result.exit_code == 1


def test_proxy_help_lists_subcommands(runner: CliRunner) -> None:
    result = runner.invoke(app, ["0tpe", "--help"])

    assert result.exit_code == 0
    assert "server-info" in result.stdout
    assert "client-config" in result.stdout
    assert "show-config" in result.stdout


def test_proxy_help_lists_fetch_certs(runner: CliRunner) -> None:
    result = runner.invoke(app, ["0tpe", "--help"])

    assert result.exit_code == 0
    assert "fetch-certs" in result.stdout
