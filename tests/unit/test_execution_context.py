from __future__ import annotations

import pytest

from zerosys.backends.base import BackendContext
from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FirewallConfig,
    ServerConfig,
)
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.planner.planner import build_plan

pytestmark = pytest.mark.unit


def _config() -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="x"),
        firewall=FirewallConfig(default="deny", allow=[22]),
    )


def test_default_execution_options() -> None:
    options = ExecutionOptions()

    assert options.dry_run is False
    assert options.verbose is False
    assert options.stop_on_failure is True
    assert options.tags == []


def test_execution_context_exposes_options() -> None:
    plan = build_plan(_config())
    backend_context = BackendContext(target_host="localhost")
    options = ExecutionOptions(
        dry_run=True,
        verbose=True,
        tags=["server"],
    )
    context = ExecutionContext(
        plan=plan,
        backend_context=backend_context,
        options=options,
    )

    assert context.dry_run is True
    assert context.verbose is True
    assert context.options.tags == ["server"]


def test_execution_context_default_options() -> None:
    plan = build_plan(_config())
    backend_context = BackendContext(target_host="localhost")
    context = ExecutionContext(plan=plan, backend_context=backend_context)

    assert context.dry_run is False
    assert context.verbose is False
