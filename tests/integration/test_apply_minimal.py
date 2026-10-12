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


def _write_config(path: Path) -> None:
    path.write_text(
        "version: 1\npackages:\n  install: [curl]\nfirewall:\n  default: deny\n  allow: [22]\n",
        encoding="utf-8",
    )


def test_apply_minimal_config(ssh_target: SshTarget, tmp_path: Path) -> None:
    config_path = tmp_path / "0sys.yaml"
    _write_config(config_path)

    config = load_config(config_path)
    plan = build_plan(config)

    assert plan.size() > 0
    assert any(t.kind.value == "packages.install" for t in plan.tasks())

    backend_context = BackendContext(
        target_host=ssh_target.host,
        target_user=ssh_target.user,
        target_port=ssh_target.port,
        ssh_key=str(ssh_target.key_path),
    )
    options = ExecutionOptions()
    context = ExecutionContext(
        plan=plan,
        backend_context=backend_context,
        options=options,
    )

    executor = Executor(context)
    state = executor.execute()

    assert state.failed == 0, f"Task failures: {state.failed_tasks}"
    assert state.successful == state.total

    result = ssh_target.run("command -v curl")
    assert result.returncode == 0, "curl should be installed"
