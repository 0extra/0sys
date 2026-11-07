from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.backends.base import BackendContext
from zerosys.core.config.parser import load_config
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.executor import Executor
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.planner import build_plan
from zerosys.core.planner.task import TaskStatus

from .conftest import SshTarget

pytestmark = [pytest.mark.integration, pytest.mark.slow]


def _run_apply(config_path: Path, target: SshTarget) -> ExecutionState:
    config = load_config(config_path)
    plan = build_plan(config)
    backend_context = BackendContext(
        target_host=target.host,
        target_user=target.user,
        target_port=target.port,
        ssh_key=str(target.key_path),
    )
    context = ExecutionContext(
        plan=plan,
        backend_context=backend_context,
        options=ExecutionOptions(),
    )
    executor = Executor(context)
    state = executor.execute()
    assert state.failed == 0, f"Task failures: {state.failed_tasks}"
    return state


def _changed_count(state: ExecutionState) -> int:
    return sum(
        1
        for task in state.executed_tasks
        if task.status is TaskStatus.SUCCESS and task.result is not None and task.result.changed
    )


def test_apply_is_idempotent(ssh_target: SshTarget, tmp_path: Path) -> None:
    config_path = tmp_path / "0sys.yaml"
    config_path.write_text(
        "version: 1\npackages:\n  install: [curl]\nfirewall:\n  default: deny\n  allow: [22]\n",
        encoding="utf-8",
    )

    first_state = _run_apply(config_path, ssh_target)
    assert first_state.successful > 0
    assert _changed_count(first_state) > 0, "first apply should report at least one changed task"

    second_state = _run_apply(config_path, ssh_target)
    assert second_state.successful == first_state.successful
    assert _changed_count(second_state) == 0, (
        f"second apply should be idempotent, but {_changed_count(second_state)} task(s) "
        f"reported changes: "
        f"{[t.name for t in second_state.executed_tasks if t.result and t.result.changed]}"
    )
