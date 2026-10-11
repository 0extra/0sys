from __future__ import annotations

from zerosys.core.planner.task import Task, TaskKind, TaskResult, TaskStatus
from zerosys.core.state.models import RunRecord, TaskRecord

pytestmark = []


def test_run_record_defaults() -> None:
    record = RunRecord()

    assert record.id
    assert record.status is TaskStatus.RUNNING
    assert record.target_host == "localhost"
    assert record.total_tasks == 0
    assert record.dry_run is False
    assert record.finished_at is None


def test_run_record_finish_sets_fields() -> None:
    record = RunRecord()
    record.finish(TaskStatus.SUCCESS)

    assert record.status is TaskStatus.SUCCESS
    assert record.finished_at is not None


def test_run_record_to_row_roundtrip() -> None:
    record = RunRecord(
        target_host="host-1",
        target_user="admin",
        total_tasks=3,
        dry_run=True,
    )
    record.finish(TaskStatus.SUCCESS)

    row = record.to_row()
    restored = RunRecord.from_row(row)

    assert restored.id == record.id
    assert restored.target_host == "host-1"
    assert restored.target_user == "admin"
    assert restored.total_tasks == 3
    assert restored.dry_run is True
    assert restored.status is TaskStatus.SUCCESS


def test_task_record_to_row_roundtrip() -> None:
    record = TaskRecord(
        run_id="run-1",
        task_id="t1",
        kind=TaskKind.SERVER,
        name="configure_server",
        target="web-01",
        backend="ansible",
        status=TaskStatus.SUCCESS,
        message="done",
        changed=True,
        duration_ms=12,
        params={"hostname": "web-01"},
    )

    row = record.to_row()
    restored = TaskRecord.from_row(row)

    assert restored.run_id == "run-1"
    assert restored.task_id == "t1"
    assert restored.kind is TaskKind.SERVER
    assert restored.status is TaskStatus.SUCCESS
    assert restored.changed is True
    assert restored.params == {"hostname": "web-01"}


def test_task_record_from_task_maps_fields() -> None:
    task = Task(kind=TaskKind.USER, name="user_admin", target="admin")
    task.backend = "ansible"
    task.mark_running()
    task.mark_success(TaskResult(status=TaskStatus.SUCCESS, message="created", changed=True))

    record = TaskRecord.from_task("run-x", task)

    assert record.run_id == "run-x"
    assert record.task_id == task.id
    assert record.kind is TaskKind.USER
    assert record.status is TaskStatus.SUCCESS
    assert record.message == "created"
    assert record.changed is True
    assert record.backend == "ansible"


def test_task_record_from_row_handles_bad_params() -> None:
    record = TaskRecord(
        run_id="run-1",
        task_id="t1",
        kind=TaskKind.SERVER,
        name="x",
    )
    row = list(record.to_row())
    row[15] = "not-json"

    restored = TaskRecord.from_row(tuple(row))

    assert restored.params == {}


def test_task_record_from_row_handles_null_params() -> None:
    record = TaskRecord(
        run_id="run-1",
        task_id="t1",
        kind=TaskKind.SERVER,
        name="x",
    )
    row = list(record.to_row())
    row[15] = None

    restored = TaskRecord.from_row(tuple(row))

    assert restored.params == {}
