from __future__ import annotations

import pytest

from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FirewallConfig,
    PackagesConfig,
    ProxyConfig,
)
from zerosys.core.config.validator import validate
from zerosys.core.planner.planner import build_plan
from zerosys.core.planner.task import TaskKind

pytestmark = pytest.mark.unit


def test_no_proxy_task_when_disabled() -> None:
    config = Config(
        version=CONFIG_VERSION,
        proxy=ProxyConfig(enabled=False),
    )
    plan = build_plan(config)

    names = [t.name for t in plan.tasks()]
    assert "configure_proxy" not in names


def test_proxy_task_created_when_enabled() -> None:
    config = Config(
        version=CONFIG_VERSION,
        proxy=ProxyConfig(enabled=True, port=8443),
    )
    plan = build_plan(config)

    proxy_tasks = [t for t in plan.tasks() if t.kind is TaskKind.PROXY]
    assert len(proxy_tasks) == 1
    task = proxy_tasks[0]
    assert task.params["port"] == 8443
    assert task.params["sni"] == "www.microsoft.com"


def test_proxy_task_depends_on_packages() -> None:
    config = Config(
        version=CONFIG_VERSION,
        packages=PackagesConfig(install=["docker.io"]),
        proxy=ProxyConfig(enabled=True),
    )
    plan = build_plan(config)
    graph = plan.graph

    install = next(t for t in graph.tasks() if t.kind is TaskKind.PACKAGES_INSTALL)
    proxy = next(t for t in graph.tasks() if t.kind is TaskKind.PROXY)

    assert install.id in graph.dependencies_of(proxy.id)


def test_proxy_task_depends_on_firewall_if_no_packages() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22, 8443]),
        proxy=ProxyConfig(enabled=True, port=8443),
    )
    plan = build_plan(config)
    graph = plan.graph

    firewall = next(t for t in graph.tasks() if t.kind is TaskKind.FIREWALL)
    proxy = next(t for t in graph.tasks() if t.kind is TaskKind.PROXY)

    assert firewall.id in graph.dependencies_of(proxy.id)


def test_proxy_backend_is_ansible() -> None:
    config = Config(
        version=CONFIG_VERSION,
        proxy=ProxyConfig(enabled=True),
    )
    plan = build_plan(config)
    proxy = next(t for t in plan.tasks() if t.kind is TaskKind.PROXY)

    assert proxy.backend == "ansible"


def test_validator_warns_when_proxy_port_closed() -> None:
    config = Config(
        version=CONFIG_VERSION,
        proxy=ProxyConfig(enabled=True, port=8443),
        firewall=FirewallConfig(default="deny", allow=[22]),
    )
    report = validate(config)

    codes = {i.code for i in report.issues}
    assert "PROXY001" in codes


def test_validator_no_warning_when_port_allowed() -> None:
    config = Config(
        version=CONFIG_VERSION,
        proxy=ProxyConfig(enabled=True, port=8443),
        firewall=FirewallConfig(default="deny", allow=[22, 8443]),
    )
    report = validate(config)

    codes = {i.code for i in report.issues}
    assert "PROXY001" not in codes


def test_proxy_task_carries_commit_sha() -> None:
    config = Config(
        version=CONFIG_VERSION,
        proxy=ProxyConfig(enabled=True, commit_sha="a1b2c3d4e5f6"),
    )
    plan = build_plan(config)
    proxy = next(t for t in plan.tasks() if t.kind is TaskKind.PROXY)

    assert proxy.params["commit_sha"] == "a1b2c3d4e5f6"


def test_proxy_task_omits_commit_sha_when_none() -> None:
    config = Config(
        version=CONFIG_VERSION,
        proxy=ProxyConfig(enabled=True),
    )
    plan = build_plan(config)
    proxy = next(t for t in plan.tasks() if t.kind is TaskKind.PROXY)

    assert "commit_sha" not in proxy.params
