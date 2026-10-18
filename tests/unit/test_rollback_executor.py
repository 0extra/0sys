from __future__ import annotations

import pytest

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.registry import get_registry
from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FileEntry,
    FirewallConfig,
    PackagesConfig,
    ServerConfig,
    UserConfig,
)
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.rollback import (
    Rollbacker,
    RollbackOptions,
    rollback,
)
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.planner import build_plan
from zerosys.core.planner.task import Task, TaskKind, TaskResult, TaskStatus

pytestmark = pytest.mark.unit


class _FakeBackend(Backend):
    def __init__(self, name: str = "ansible") -> None:
        self.name = name
        self.rollback_calls: list[str] = []
        self.rollback_status = TaskStatus.SUCCESS

    def supports(self, task: Task) -> bool:
        return True

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(status=TaskStatus.SUCCESS)

    def can_rollback(self, task: Task) -> bool:
        return task.kind in {
            TaskKind.FILE,
            TaskKind.USER,
            TaskKind.SERVICE,
            TaskKind.PACKAGES_INSTALL,
        }

    def rollback(self, task: Task, context: BackendContext) -> TaskResult:
        self.rollback_calls.append(task.name)
        return TaskResult(status=self.rollback_status, message="undone")


@pytest.fixture
def fake_backend() -> _FakeBackend:
    backend = _FakeBackend("ansible")
    registry = get_registry()
    original = registry._backends.get("ansible")
    registry.register(backend)
    yield backend
    if original is not None:
        registry.register(original)
    else:
        registry._backends.pop("ansible", None)


def _config_with_files() -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="test"),
        firewall=FirewallConfig(default="deny", allow=[22]),
        users=[UserConfig(name="admin", groups=["sudo"], sudo=True)],
        files=[
            FileEntry(src="./x", dest="/etc/x/x.conf"),
            FileEntry(src="./y", dest="/etc/y/y.conf"),
        ],
    )


def _config_with_packages() -> Config:
    return Config(
        version=CONFIG_VERSION,
        packages=PackagesConfig(install=["nginx"]),
    )


def _context(config: Config) -> ExecutionContext:
    plan = build_plan(config)
    return ExecutionContext(
        plan=plan,
        backend_context=BackendContext(target_host="localhost"),
        options=ExecutionOptions(),
    )


def test_rollback_returns_report(fake_backend: _FakeBackend) -> None:
    config = _config_with_files()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    report = Rollbacker(context, state).rollback()

    assert report.attempted > 0


def test_rollback_skips_not_reversible(fake_backend: _FakeBackend) -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22]),
    )
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    report = Rollbacker(context, state).rollback()

    assert report.not_reversible
    assert report.successful == 0


def test_rollback_default_holds_packages(fake_backend: _FakeBackend) -> None:
    config = _config_with_packages()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    report = Rollbacker(context, state).rollback()

    assert "install_packages" in report.not_reversible
    assert report.successful == 0


def test_rollback_aggressive_removes_packages(fake_backend: _FakeBackend) -> None:
    config = _config_with_packages()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    report = Rollbacker(context, state, RollbackOptions(aggressive=True)).rollback()

    assert report.successful >= 1
    assert "install_packages" in fake_backend.rollback_calls


def test_rollback_calls_backend_in_reverse(fake_backend: _FakeBackend) -> None:
    config = _config_with_files()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    Rollbacker(context, state).rollback()

    assert len(fake_backend.rollback_calls) >= 1


def test_rollback_marks_tasks(fake_backend: _FakeBackend) -> None:
    config = _config_with_files()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    Rollbacker(context, state).rollback()

    assert state.rolled_back >= 1


def test_rollback_noop_when_nothing_executed(fake_backend: _FakeBackend) -> None:
    config = _config_with_files()
    context = _context(config)
    state = ExecutionState(total=0)

    report = Rollbacker(context, state).rollback()

    assert report.attempted == 0
    assert report.successful == 0


def test_rollback_shortcut(fake_backend: _FakeBackend) -> None:
    config = _config_with_files()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    report = rollback(context, state)

    assert report.attempted >= 1


def test_rollback_skips_non_idempotent(fake_backend: _FakeBackend) -> None:
    config = _config_with_files()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        task.idempotent = False
        state.register_success(task)

    report = Rollbacker(context, state).rollback()

    assert report.attempted == 0


def test_rollback_stops_on_failure_when_configured(
    fake_backend: _FakeBackend,
) -> None:
    fake_backend.rollback_status = TaskStatus.FAILED
    config = _config_with_files()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    report = Rollbacker(context, state, RollbackOptions(stop_on_failure=True)).rollback()

    assert report.failed >= 1
    assert len(fake_backend.rollback_calls) == 1


def test_rollback_report_summary(fake_backend: _FakeBackend) -> None:
    config = _config_with_files()
    context = _context(config)
    state = ExecutionState(total=0)
    for task in context.plan.tasks():
        state.register_success(task)

    report = Rollbacker(context, state).rollback()
    summary = report.summary()

    assert "rolled back" in summary
    assert "not reversible" in summary


def test_rollback_aggressive_skips_unchanged() -> None:
    registry = get_registry()
    original = registry._backends.get("fake_ansible")
    fake_backend = _FakeBackend("fake_ansible")
    registry.register(fake_backend)

    try:
        task = Task(kind=TaskKind.USER, name="user_testuser3", backend="fake_ansible")
        task.mark_success(TaskResult(status=TaskStatus.SUCCESS, changed=False))

        state = ExecutionState(total=1)
        state.register_success(task)

        class _FakeContext:
            backend_context = BackendContext(target_host="localhost")

        rollbacker_normal = Rollbacker(_FakeContext(), state, RollbackOptions(aggressive=False))
        report_normal = rollbacker_normal.rollback()
        assert report_normal.successful == 0
        assert report_normal.skipped == 1

        rollbacker_aggressive = Rollbacker(_FakeContext(), state, RollbackOptions(aggressive=True))
        report_aggressive = rollbacker_aggressive.rollback()
        assert report_aggressive.successful == 0
        assert report_aggressive.skipped == 1
        assert fake_backend.rollback_calls == []
    finally:
        if original is not None:
            registry.register(original)
        else:
            registry._backends.pop("fake_ansible", None)


def test_rollback_aggressive_removes_only_changed() -> None:
    registry = get_registry()
    original = registry._backends.get("fake_ansible")
    fake_backend = _FakeBackend("fake_ansible")
    registry.register(fake_backend)

    try:
        changed_task = Task(kind=TaskKind.USER, name="user_changed", backend="fake_ansible")
        changed_task.mark_success(TaskResult(status=TaskStatus.SUCCESS, changed=True))

        unchanged_task = Task(kind=TaskKind.USER, name="user_unchanged", backend="fake_ansible")
        unchanged_task.mark_success(TaskResult(status=TaskStatus.SUCCESS, changed=False))

        state = ExecutionState(total=2)
        state.register_success(changed_task)
        state.register_success(unchanged_task)

        class _FakeContext:
            backend_context = BackendContext(target_host="localhost")

        report = Rollbacker(_FakeContext(), state, RollbackOptions(aggressive=True)).rollback()

        assert report.successful == 1
        assert report.skipped == 1
        assert fake_backend.rollback_calls == ["user_changed"]
    finally:
        if original is not None:
            registry.register(original)
        else:
            registry._backends.pop("fake_ansible", None)


def test_rollback_twice_is_idempotent() -> None:
    registry = get_registry()
    original = registry._backends.get("fake_ansible")
    fake_backend = _FakeBackend("fake_ansible")
    registry.register(fake_backend)

    try:
        task = Task(kind=TaskKind.USER, name="user_x", backend="fake_ansible")
        task.mark_success(TaskResult(status=TaskStatus.SUCCESS, changed=True))

        state = ExecutionState(total=1)
        state.register_success(task)

        class _FakeContext:
            backend_context = BackendContext(target_host="localhost")

        first = Rollbacker(_FakeContext(), state, RollbackOptions(aggressive=True)).rollback()
        assert first.successful == 1
        assert fake_backend.rollback_calls == ["user_x"]

        second = Rollbacker(_FakeContext(), state, RollbackOptions(aggressive=True)).rollback()
        assert second.successful == 0
        assert second.skipped == 1
        assert fake_backend.rollback_calls == ["user_x"]
    finally:
        if original is not None:
            registry.register(original)
        else:
            registry._backends.pop("fake_ansible", None)
