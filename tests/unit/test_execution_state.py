from __future__ import annotations

import pytest

from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.task import Task, TaskKind, TaskStatus

pytestmark = pytest.mark.unit


def _task(name: str) -> Task:
    return Task(kind=TaskKind.COMMAND, name=name)


def test_initial_state() -> None:
    state = ExecutionState(total=5)

    assert state.total == 5
    assert state.completed == 0
    assert state.successful == 0
    assert state.failed == 0
    assert state.skipped == 0
    assert state.rolled_back == 0


def test_register_success_increments_counters() -> None:
    state = ExecutionState(total=1)
    task = _task("a")

    state.register_success(task)

    assert state.completed == 1
    assert state.successful == 1
    assert task in state.executed_tasks


def test_register_failure_increments_counters() -> None:
    state = ExecutionState(total=1)
    task = _task("a")

    state.register_failure(task)

    assert state.completed == 1
    assert state.failed == 1
    assert task in state.failed_tasks


def test_register_skip_increments_counters() -> None:
    state = ExecutionState(total=1)
    task = _task("a")

    state.register_skip(task)

    assert state.completed == 1
    assert state.skipped == 1
    assert task in state.skipped_tasks


def test_register_rollback_increments_counters() -> None:
    state = ExecutionState(total=1)
    task = _task("a")

    state.register_rollback(task)

    assert state.rolled_back == 1
    assert task in state.rolled_back_tasks


def test_has_failures() -> None:
    state = ExecutionState(total=1)
    assert not state.has_failures()

    state.register_failure(_task("a"))
    assert state.has_failures()


def test_final_status_all_success() -> None:
    state = ExecutionState(total=2)
    state.register_success(_task("a"))
    state.register_success(_task("b"))

    assert state.final_status() is TaskStatus.SUCCESS


def test_final_status_failure() -> None:
    state = ExecutionState(total=1)
    state.register_failure(_task("a"))

    assert state.final_status() is TaskStatus.FAILED


def test_final_status_empty_run() -> None:
    state = ExecutionState(total=0)

    assert state.final_status() is TaskStatus.SKIPPED


def test_summary_format() -> None:
    state = ExecutionState(total=3)
    state.register_success(_task("a"))
    state.register_failure(_task("b"))
    state.register_skip(_task("c"))

    summary = state.summary()

    assert "1 ok" in summary
    assert "1 failed" in summary
    assert "1 skipped" in summary
    assert "of 3" in summary
