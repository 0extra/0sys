from __future__ import annotations

import pytest

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.registry import get_registry
from zerosys.core.config.schema import CONFIG_VERSION, Config, FirewallConfig
from zerosys.core.config.validator import validate
from zerosys.core.executor.rollback import Rollbacker, RollbackOptions
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.task import Task, TaskKind, TaskResult, TaskStatus
from zerosys.core.security.secrets import redact_dict, redact_text

pytestmark = pytest.mark.unit


def test_fw005_blocks_custom_connection_port() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22]),
    )
    report = validate(config, connect_port=2222)
    codes = {i.code for i in report.issues}
    assert "FW005" in codes


def test_fw005_allows_correct_port() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[2222]),
    )
    report = validate(config, connect_port=2222)
    codes = {i.code for i in report.issues}
    assert "FW005" not in codes


def test_redact_text_multiple_secrets() -> None:
    text = "connecting to db with password=supersecret and token=12345"
    result = redact_text(text)
    assert "supersecret" not in result
    assert "12345" not in result
    assert "password=" in result


def test_redact_dict_nested_list() -> None:
    data = {"users": [{"name": "admin", "password": "secret1"}]}
    result = redact_dict(data)
    assert "secret1" not in str(result)
    assert result["users"][0]["name"] == "admin"


class _FakeRollbackBackend(Backend):
    name = "fake_ansible"

    def supports(self, task: Task) -> bool:
        return True

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(status=TaskStatus.SUCCESS)

    def can_rollback(self, task: Task) -> bool:
        return True

    def rollback(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(status=TaskStatus.SUCCESS, message="undone")


def test_rollback_aggressive_bypasses_changed_flag() -> None:
    registry = get_registry()
    original = registry._backends.get("fake_ansible")
    fake_backend = _FakeRollbackBackend()
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
        assert report_aggressive.successful == 1
    finally:
        if original is not None:
            registry.register(original)
        else:
            registry._backends.pop("fake_ansible", None)
