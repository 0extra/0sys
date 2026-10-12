from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.backends.base import BackendContext
from zerosys.core.config.parser import load_config
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.executor import Executor
from zerosys.core.planner.planner import build_plan

from .conftest import SshTarget

pytestmark = [pytest.mark.integration, pytest.mark.slow]


def _run_apply(config_path: Path, target: SshTarget) -> int:
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
    return state.successful


def test_apply_is_idempotent(ssh_target: SshTarget, tmp_path: Path) -> None:
    config_path = tmp_path / "0sys.yaml"
    config_path.write_text(
        "version: 1\npackages:\n  install: [curl]\nfirewall:\n  default: deny\n  allow: [22]\n",
        encoding="utf-8",
    )

    first_count = _run_apply(config_path, ssh_target)
    assert first_count > 0

    second_count = _run_apply(config_path, ssh_target)
    assert second_count == first_count
