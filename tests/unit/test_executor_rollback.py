from __future__ import annotations

import pytest

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.registry import get_registry
from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FirewallConfig,
    ServerConfig,
)
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.rollback import Rollbacker, rollback
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.planner import build_plan
from zerosys.core.planner.task import Task, TaskResult, TaskStatus

pytestmark = pytest.mark.unit


class _RollbackBackend(Backend):
    def __init__(self, name: str = "ansible") -> None:
        self.name = name
        self.description = "supports rollback"
        self.rolled_back: list[str] = []

    def supports(self, task: Task) -> bool:
        return True

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(status=TaskStatus.SUCCESS)

    def rollback(self, task: Task, context: BackendContext) -> TaskResult:
        self.rolled_back.append(task.name)
        return TaskResult(status=TaskStatus.ROLLED_BACK, message="undone")


@pytest.fixture
def rollback_backend() -> _RollbackBackend:
    backend = _RollbackBackend("ansible")
    registry = get_registry()
    original = registry._backends.get("ansible")
    registry.register(backend)
    yield backend
    if original is not None:
        registry.register(original)
    else:
        registry._backends.pop("ansible", None)


def _config() -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="x"),
        firewall=FirewallConfig(default="deny", allow=[22]),
    )


def test_rollback_calls_backend_in_reverse_order(
    rollback_backend: _RollbackBackend,
) -> None:
    plan = build_plan(_config())
    context = ExecutionContext(
        plan=plan,
        backend_context=BackendContext(target_host="localhost"),
        options=ExecutionOptions(),
    )
    state = ExecutionState(total=2)

    tasks = plan.tasks()
    for task in tasks:
        task.backend = "ansible"
        state.register_success(task)

    Rollbacker(context, state).rollback()

    assert rollback_backend.rolled_back == ["configure_firewall", "configure_server"]


def test_rollback_marks_tasks(
    rollback_backend: _RollbackBackend,
) -> None:
    plan = build_plan(_config())
    context = ExecutionContext(
        plan=plan,
        backend_context=BackendContext(target_host="localhost"),
        options=ExecutionOptions(),
    )
    state = ExecutionState(total=1)
    task = plan.tasks()[0]
    task.backend = "ansible"
    state.register_success(task)

    Rollbacker(context, state).rollback()

    assert task.status is TaskStatus.ROLLED_BACK
    assert state.rolled_back == 1


def test_rollback_function_shortcut(
    rollback_backend: _RollbackBackend,
) -> None:
    plan = build_plan(_config())
    context = ExecutionContext(
        plan=plan,
        backend_context=BackendContext(target_host="localhost"),
        options=ExecutionOptions(),
    )
    state = ExecutionState(total=1)
    task = plan.tasks()[0]
    task.backend = "ansible"
    state.register_success(task)

    result = rollback(context, state)

    assert result.rolled_back == 1


def test_rollback_noop_when_nothing_executed() -> None:
    plan = build_plan(_config())
    context = ExecutionContext(
        plan=plan,
        backend_context=BackendContext(target_host="localhost"),
        options=ExecutionOptions(),
    )
    state = ExecutionState(total=0)

    result = rollback(context, state)

    assert result.rolled_back == 0


def test_rollback_skips_non_idempotent_tasks(
    rollback_backend: _RollbackBackend,
) -> None:
    plan = build_plan(_config())
    context = ExecutionContext(
        plan=plan,
        backend_context=BackendContext(target_host="localhost"),
        options=ExecutionOptions(),
    )
    state = ExecutionState(total=1)
    task = plan.tasks()[0]
    task.backend = "ansible"
    task.idempotent = False
    state.register_success(task)

    Rollbacker(context, state).rollback()

    assert rollback_backend.rolled_back == []
