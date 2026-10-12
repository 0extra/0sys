from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.backends.base import BackendContext
from zerosys.core.config.parser import load_config
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.executor import Executor
from zerosys.core.executor.rollback import Rollbacker
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.planner import build_plan

from .conftest import SshTarget

pytestmark = [pytest.mark.integration, pytest.mark.slow]


def test_rollback_removes_user(ssh_target: SshTarget, tmp_path: Path) -> None:
    config_path = tmp_path / "0sys.yaml"
    config_path.write_text(
        "version: 1\n"
        "users:\n"
        "  - name: rollbackuser\n"
        "    groups: []\n"
        "    shell: /bin/sh\n"
        "firewall:\n"
        "  default: deny\n"
        "  allow: [22]\n",
        encoding="utf-8",
    )

    config = load_config(config_path)
    plan = build_plan(config)
    backend_context = BackendContext(
        target_host=ssh_target.host,
        target_user=ssh_target.user,
        target_port=ssh_target.port,
        ssh_key=str(ssh_target.key_path),
    )
    context = ExecutionContext(
        plan=plan,
        backend_context=backend_context,
        options=ExecutionOptions(),
    )

    executor = Executor(context)
    state = executor.execute()
    assert state.failed == 0, f"Task failures: {state.failed_tasks}"

    exists_before = ssh_target.run("id rollbackuser").returncode == 0
    assert exists_before, "user should exist after apply"

    rollback_state = ExecutionState(total=state.total)
    for task in state.executed_tasks:
        rollback_state.register_success(task)

    report = Rollbacker(context, rollback_state).rollback()

    assert report.failed == 0
    assert report.successful >= 1

    exists_after = ssh_target.run("id rollbackuser").returncode == 0
    assert not exists_after, "user should be removed after rollback"
