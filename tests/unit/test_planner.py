from __future__ import annotations

import pytest

from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FirewallConfig,
    PackagesConfig,
    ServerConfig,
    ServiceConfig,
    UserConfig,
)
from zerosys.core.planner.planner import Plan, Planner, build_plan
from zerosys.core.planner.resolver import BACKEND_ANSIBLE, BACKEND_SHELL
from zerosys.core.planner.task import TaskKind

pytestmark = pytest.mark.unit


def _names(plan: Plan) -> list[str]:
    return [task.name for task in plan.tasks()]


def test_build_plan_empty_config() -> None:
    config = Config(version=CONFIG_VERSION)
    plan = build_plan(config)

    assert plan.size() == 0
    assert plan.tasks() == []


def test_build_plan_minimal_config(sample_config: Config) -> None:
    plan = build_plan(sample_config)
    names = _names(plan)

    assert "configure_server" in names
    assert "configure_firewall" in names
    assert plan.size() == 2


def test_build_plan_web_config(web_config: Config) -> None:
    plan = build_plan(web_config)

    assert plan.size() >= 4
    assert "install_packages" in _names(plan)
    assert "service_nginx" in _names(plan)


def test_firewall_depends_on_packages() -> None:
    config = Config(
        version=CONFIG_VERSION,
        packages=PackagesConfig(install=["ufw"]),
        firewall=FirewallConfig(default="deny", allow=[22]),
    )
    plan = build_plan(config)
    graph = plan.graph

    install = next(t for t in graph.tasks() if t.kind is TaskKind.PACKAGES_INSTALL)
    firewall = next(t for t in graph.tasks() if t.kind is TaskKind.FIREWALL)

    assert install.id in graph.dependencies_of(firewall.id)


def test_users_depend_on_firewall() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22]),
        users=[UserConfig(name="admin", groups=["sudo"], sudo=True)],
    )
    plan = build_plan(config)
    graph = plan.graph

    firewall = next(t for t in graph.tasks() if t.kind is TaskKind.FIREWALL)
    user = next(t for t in graph.tasks() if t.kind is TaskKind.USER)

    assert firewall.id in graph.dependencies_of(user.id)


def test_services_depend_on_firewall() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22]),
        services={"nginx": ServiceConfig()},
    )
    plan = build_plan(config)
    graph = plan.graph

    firewall = next(t for t in graph.tasks() if t.kind is TaskKind.FIREWALL)
    service = next(t for t in graph.tasks() if t.kind is TaskKind.SERVICE)

    assert firewall.id in graph.dependencies_of(service.id)


def test_commands_have_no_dependencies() -> None:
    config = Config(
        version=CONFIG_VERSION,
        commands=[{"name": "deploy", "run": "echo hi"}],  # type: ignore[list-item]
    )
    plan = build_plan(config)
    command = next(t for t in plan.graph.tasks() if t.kind is TaskKind.COMMAND)

    assert command.depends_on == []


def test_backend_resolver_assigns_ansible_to_server(sample_config: Config) -> None:
    plan = build_plan(sample_config)

    for task in plan.tasks():
        assert task.backend == BACKEND_ANSIBLE


def test_backend_resolver_assigns_shell_to_commands() -> None:
    config = Config(
        version=CONFIG_VERSION,
        commands=[{"name": "deploy", "run": "echo hi"}],  # type: ignore[list-item]
    )
    plan = build_plan(config)
    command = next(t for t in plan.tasks() if t.kind is TaskKind.COMMAND)

    assert command.backend == BACKEND_SHELL


def test_forced_backend_overrides_default(web_config: Config) -> None:
    plan = build_plan(web_config, forced_backend=BACKEND_SHELL)

    assert all(task.backend == BACKEND_SHELL for task in plan.tasks())


def test_plan_levels_deterministic(web_config: Config) -> None:
    planner = Planner()
    first = planner.build(web_config)
    second = planner.build(web_config)

    first_names = [[t.name for t in level] for level in first.levels()]
    second_names = [[t.name for t in level] for level in second.levels()]

    assert first_names == second_names


def test_plan_summary_counts_by_backend(web_config: Config) -> None:
    plan = build_plan(web_config)
    summary = plan.summary()

    assert summary.get(BACKEND_ANSIBLE, 0) == plan.size()


def test_task_ids_are_unique(web_config: Config) -> None:
    plan = build_plan(web_config)
    ids = [task.id for task in plan.tasks()]

    assert len(ids) == len(set(ids))


def test_server_task_contains_hostname() -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="my-vps", timezone="UTC"),
    )
    plan = build_plan(config)
    server = next(t for t in plan.tasks() if t.kind is TaskKind.SERVER)

    assert server.params["hostname"] == "my-vps"
    assert server.params["timezone"] == "UTC"
