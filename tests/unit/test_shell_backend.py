from __future__ import annotations

import pytest

from zerosys.backends.base import BackendContext
from zerosys.backends.shell.backend import ShellBackend
from zerosys.core.errors import BackendError
from zerosys.core.planner.task import Task, TaskKind, TaskStatus

pytestmark = pytest.mark.unit


@pytest.fixture
def backend() -> ShellBackend:
    return ShellBackend()


@pytest.fixture
def context() -> BackendContext:
    return BackendContext(target_host="localhost")


def test_supports_command_tasks(backend: ShellBackend) -> None:
    task = Task(kind=TaskKind.COMMAND, name="x", params={"run": "true"})

    assert backend.supports(task) is True


def test_does_not_support_other_kinds(backend: ShellBackend) -> None:
    task = Task(kind=TaskKind.SERVER, name="x")

    assert backend.supports(task) is False


def test_run_dry_run_does_not_execute(
    backend: ShellBackend,
    context: BackendContext,
) -> None:
    context.dry_run = True
    task = Task(kind=TaskKind.COMMAND, name="x", params={"run": "exit 1"})

    result = backend.run(task, context)

    assert result.status is TaskStatus.SUCCESS
    assert result.changed is False
    assert "[dry-run]" in result.message


def test_run_successful_command(
    backend: ShellBackend,
    context: BackendContext,
) -> None:
    task = Task(kind=TaskKind.COMMAND, name="x", params={"run": "echo hello"})

    result = backend.run(task, context)

    assert result.status is TaskStatus.SUCCESS
    assert result.changed is True
    assert "hello" in result.stdout


def test_run_failing_command(
    backend: ShellBackend,
    context: BackendContext,
) -> None:
    task = Task(kind=TaskKind.COMMAND, name="x", params={"run": "exit 7"})

    result = backend.run(task, context)

    assert result.status is TaskStatus.FAILED
    assert "7" in result.message


def test_run_missing_command_raises(
    backend: ShellBackend,
    context: BackendContext,
) -> None:
    task = Task(kind=TaskKind.COMMAND, name="x")

    with pytest.raises(BackendError, match="no 'run' parameter"):
        backend.run(task, context)


def test_run_unsupported_kind_raises(
    backend: ShellBackend,
    context: BackendContext,
) -> None:
    task = Task(kind=TaskKind.SERVER, name="x")

    with pytest.raises(BackendError, match="does not support"):
        backend.run(task, context)


def test_check_returns_skipped_for_unsupported(
    backend: ShellBackend,
    context: BackendContext,
) -> None:
    task = Task(kind=TaskKind.SERVER, name="x")

    result = backend.check(task, context)

    assert result.status is TaskStatus.SKIPPED


def test_check_returns_success_for_supported(
    backend: ShellBackend,
    context: BackendContext,
) -> None:
    task = Task(kind=TaskKind.COMMAND, name="x", params={"run": "true"})

    result = backend.check(task, context)

    assert result.status is TaskStatus.SUCCESS
    assert result.changed is False
