from __future__ import annotations

import pytest

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.registry import get_registry
from zerosys.core.config.schema import (
    Config,
)
from zerosys.core.errors import ExecutorError
from zerosys.core.executor import executor as executor_module
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.executor import Executor
from zerosys.core.planner.planner import build_plan
from zerosys.core.planner.task import Task, TaskResult, TaskStatus

pytestmark = pytest.mark.unit


class _RecordingBackend(Backend):
    def __init__(self, name: str = "recorder") -> None:
        self.name = name
        self.description = "records calls"
        self.calls: list[str] = []
        self.fail_on: set[str] = set()
        self.skip_on: set[str] = set()

    def supports(self, task: Task) -> bool:
        return True

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        self.calls.append(task.name)
        if task.name in self.fail_on:
            return TaskResult(status=TaskStatus.FAILED, message="boom")
        if task.name in self.skip_on:
            return TaskResult(status=TaskStatus.SKIPPED, message="not needed")
        return TaskResult(status=TaskStatus.SUCCESS, changed=True)


@pytest.fixture
def recording_backend() -> _RecordingBackend:
    backend = _RecordingBackend("ansible")
    registry = get_registry()
    original = registry._backends.get("ansible")
    registry.register(backend)
    yield backend
    if original is not None:
        registry.register(original)
    else:
        registry._backends.pop("ansible", None)


@pytest.fixture
def shell_backend() -> _RecordingBackend:
    backend = _RecordingBackend("shell")
    registry = get_registry()
    original = registry._backends.get("shell")
    registry.register(backend)
    yield backend
    if original is not None:
        registry.register(original)
    else:
        registry._backends.pop("shell", None)


def _context(config: Config, **options_kwargs: object) -> ExecutionContext:
    plan = build_plan(config)
    backend_context = BackendContext(target_host="localhost", dry_run=False)
    options = ExecutionOptions(**options_kwargs)  # type: ignore[arg-type]
    return ExecutionContext(plan=plan, backend_context=backend_context, options=options)


def test_executor_runs_all_tasks_successfully(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    context = _context(sample_config)
    executor = Executor(context)

    state = executor.execute()

    assert state.successful == 2
    assert state.failed == 0
    assert state.total == 2


def test_executor_marks_success_status(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    context = _context(sample_config)
    Executor(context).execute()

    for task in context.plan.tasks():
        assert task.status is TaskStatus.SUCCESS
        assert task.result is not None
        assert task.result.changed is True


def test_executor_stops_on_failure(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    recording_backend.fail_on = {"configure_server"}
    context = _context(sample_config, stop_on_failure=True)

    state = Executor(context).execute()

    assert state.failed == 1
    assert "configure_firewall" not in recording_backend.calls


def test_executor_keeps_going_when_stop_on_failure_disabled(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    recording_backend.fail_on = {"configure_server"}
    context = _context(sample_config, stop_on_failure=False)

    state = Executor(context).execute()

    assert state.failed == 1
    assert "configure_firewall" in recording_backend.calls


def test_executor_handles_skipped_tasks(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    recording_backend.skip_on = {"configure_server"}
    context = _context(sample_config)

    state = Executor(context).execute()

    assert state.skipped == 1
    assert state.successful == 1


def test_executor_filter_by_tag_matches(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    context = _context(sample_config, tags=["server"])
    for task in context.plan.tasks():
        task.tags = [task.kind.value]

    state = Executor(context).execute()

    assert state.successful == 1
    assert state.skipped == 1


def test_executor_invokes_callbacks(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    started: list[str] = []
    finished: list[str] = []

    context = _context(sample_config)
    executor = Executor(
        context,
        on_task_start=lambda task: started.append(task.name),
        on_task_finish=lambda task: finished.append(task.name),
    )

    executor.execute()

    assert started == ["configure_server", "configure_firewall"]
    assert finished == ["configure_server", "configure_firewall"]


def test_executor_raises_when_backend_missing(
    sample_config: Config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def _no_backends() -> None:
        return None

    monkeypatch.setattr(executor_module, "load_default_backends", _no_backends)

    context = _context(sample_config)
    executor = Executor(context)

    for task in context.plan.tasks():
        task.backend = "does-not-exist"

    with pytest.raises(ExecutorError, match="not registered"):
        executor.execute()


def test_executor_state_summary_format(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    context = _context(sample_config)
    state = Executor(context).execute()

    assert "2 ok" in state.summary()
    assert "0 failed" in state.summary()


def test_executor_final_status_success(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    context = _context(sample_config)
    state = Executor(context).execute()

    assert state.final_status() is TaskStatus.SUCCESS


def test_executor_final_status_failed(
    sample_config: Config,
    recording_backend: _RecordingBackend,
) -> None:
    recording_backend.fail_on = {"configure_server"}
    context = _context(sample_config)
    state = Executor(context).execute()

    assert state.final_status() is TaskStatus.FAILED
