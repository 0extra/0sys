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
def state_with_run(tmp_path: Path) -> tuple[Path, str]:
    db_path = tmp_path / "state.db"
    store = StateStore(db_path)
    store.connect()
    record = RunRecord(target_host="localhost", total_tasks=1)
    store.save_run(record)
    store.save_task(
        TaskRecord(
            run_id=record.id,
            task_id="t1",
            kind=TaskKind.FILE,
            name="file_x",
            backend="ansible",
            status=TaskStatus.SUCCESS,
            params={"src": "./x", "dest": "/etc/x.conf"},
        )
    )
    store.close()
    return db_path, record.id


def test_rollback_list_empty(runner: CliRunner, tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"

    result = runner.invoke(app, ["rollback", "--list", "--state-path", str(db_path)])

    assert result.exit_code == 0


def test_rollback_list_with_run(runner: CliRunner, state_with_run: tuple[Path, str]) -> None:
    db_path, _ = state_with_run

    result = runner.invoke(app, ["rollback", "--list", "--state-path", str(db_path)])

    assert result.exit_code == 0
    assert "Recent runs" in result.stdout


def test_rollback_dry_run(runner: CliRunner, state_with_run: tuple[Path, str]) -> None:
    db_path, run_id = state_with_run

    result = runner.invoke(
        app,
        ["rollback", run_id, "--dry-run", "--state-path", str(db_path)],
    )

    assert result.exit_code == 0
    assert "Rollback preview" in result.stdout


def test_rollback_unknown_run(runner: CliRunner, state_with_run: tuple[Path, str]) -> None:
    db_path, _ = state_with_run

    result = runner.invoke(
        app,
        ["rollback", "does-not-exist", "--dry-run", "--state-path", str(db_path)],
    )

    assert result.exit_code == 1
