from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.core.planner.task import TaskKind, TaskStatus
from zerosys.core.state.models import RunRecord, TaskRecord
from zerosys.core.state.store import StateStore

pytestmark = pytest.mark.unit


def test_store_creates_database_file(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    store = StateStore(db_path)
    store.connect()
    try:
        assert db_path.exists()
    finally:
        store.close()


def test_store_creates_parent_directories(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "deeper" / "state.db"
    store = StateStore(db_path)
    store.connect()
    try:
        assert db_path.exists()
    finally:
        store.close()


def test_save_and_get_run(store: StateStore) -> None:
    record = RunRecord(
        target_host="test-host",
        total_tasks=3,
        dry_run=False,
    )
    store.save_run(record)

    loaded = store.get_run(record.id)

    assert loaded is not None
    assert loaded.id == record.id
    assert loaded.target_host == "test-host"
    assert loaded.total_tasks == 3
    assert loaded.dry_run is False


def test_update_run_status(store: StateStore) -> None:
    record = RunRecord(target_host="h", total_tasks=1)
    store.save_run(record)

    record.successful_tasks = 1
    record.finish(TaskStatus.SUCCESS)
    store.update_run(record)

    loaded = store.get_run(record.id)
    assert loaded is not None
    assert loaded.status is TaskStatus.SUCCESS
    assert loaded.finished_at is not None


def test_latest_run_returns_most_recent(store: StateStore) -> None:
    first = RunRecord(target_host="h1", total_tasks=1)
    second = RunRecord(target_host="h2", total_tasks=2)
    store.save_run(first)
    store.save_run(second)

    latest = store.latest_run()

    assert latest is not None
    assert latest.id == second.id


def test_latest_run_empty_store(store: StateStore) -> None:
    assert store.latest_run() is None


def test_list_runs_ordered_desc(store: StateStore) -> None:
    for index in range(3):
        store.save_run(RunRecord(target_host=f"h{index}", total_tasks=index))

    runs = store.list_runs(limit=10)

    assert len(runs) == 3


def test_list_runs_respects_limit(store: StateStore) -> None:
    for index in range(5):
        store.save_run(RunRecord(target_host=f"h{index}", total_tasks=index))

    runs = store.list_runs(limit=2)

    assert len(runs) == 2


def test_save_and_get_tasks(store: StateStore) -> None:
    run = RunRecord(target_host="h", total_tasks=1)
    store.save_run(run)

    task = TaskRecord(
        run_id=run.id,
        task_id="t1",
        kind=TaskKind.SERVER,
        name="configure_server",
        status=TaskStatus.SUCCESS,
        message="done",
        changed=True,
        duration_ms=42,
    )
    store.save_task(task)

    tasks = store.get_tasks(run.id)
    assert len(tasks) == 1
    assert tasks[0].task_id == "t1"
    assert tasks[0].kind is TaskKind.SERVER
    assert tasks[0].status is TaskStatus.SUCCESS
    assert tasks[0].changed is True
    assert tasks[0].duration_ms == 42


def test_save_tasks_bulk(store: StateStore) -> None:
    run = RunRecord(target_host="h", total_tasks=2)
    store.save_run(run)

    tasks = [
        TaskRecord(
            run_id=run.id,
            task_id=f"t{i}",
            kind=TaskKind.SERVER,
            name=f"task{i}",
        )
        for i in range(2)
    ]
    store.save_tasks(tasks)

    assert len(store.get_tasks(run.id)) == 2


def test_count_runs(store: StateStore) -> None:
    assert store.count_runs() == 0
    store.save_run(RunRecord(target_host="h"))
    store.save_run(RunRecord(target_host="h"))
    assert store.count_runs() == 2


def test_store_context_manager(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"

    with StateStore(db_path) as store:
        store.save_run(RunRecord(target_host="h"))
        assert store.count_runs() == 1

    reopened = StateStore(db_path)
    try:
        reopened.connect()
        assert reopened.count_runs() == 1
    finally:
        reopened.close()


def test_get_run_returns_none_for_unknown(store: StateStore) -> None:
    assert store.get_run("does-not-exist") is None


def test_get_tasks_empty_for_new_run(store: StateStore) -> None:
    run = RunRecord(target_host="h")
    store.save_run(run)

    assert store.get_tasks(run.id) == []
