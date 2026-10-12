from __future__ import annotations

from zerosys.core.config.schema import Config
from zerosys.core.planner.dag import DependencyGraph
from zerosys.core.planner.resolver import BackendResolver
from zerosys.core.planner.task import Task, TaskKind


class Plan:
    def __init__(self, graph: DependencyGraph, resolver: BackendResolver) -> None:
        self.graph = graph
        self.resolver = resolver
        self._attach_backends()

    def _attach_backends(self) -> None:
        for task in self.graph.tasks():
            if task.backend is None:
                task.backend = self.resolver.resolve(task)

    def tasks(self) -> list[Task]:
        return self.graph.topological_order()

    def levels(self) -> list[list[Task]]:
        return self.graph.levels()

    def size(self) -> int:
        return len(self.graph)

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for task in self.graph.tasks():
            key = task.backend or "unknown"
            counts[key] = counts.get(key, 0) + 1
        return counts


class Planner:
    def __init__(self, resolver: BackendResolver | None = None) -> None:
        self.resolver = resolver or BackendResolver()

    def build(self, config: Config) -> Plan:
        graph = DependencyGraph()

        server_task = self._make_server_task(config)
        if server_task is not None:
            graph.add_task(server_task)

        package_tasks = self._make_package_tasks(config, server_task)
        for task in package_tasks:
            graph.add_task(task)

        firewall_task = self._make_firewall_task(config)
        if firewall_task is not None:
            graph.add_task(firewall_task)

        user_tasks = self._make_user_tasks(config, server_task)
        for task in user_tasks:
            graph.add_task(task)

        service_tasks = self._make_service_tasks(config, package_tasks)
        for task in service_tasks:
            graph.add_task(task)

        file_tasks = self._make_file_tasks(config, service_tasks)
        for task in file_tasks:
            graph.add_task(task)

        proxy_task = self._make_proxy_task(config)
        if proxy_task is not None:
            graph.add_task(proxy_task)

        command_tasks = self._make_command_tasks(config)
        for task in command_tasks:
            graph.add_task(task)

        install_task = next(
            (t for t in package_tasks if t.kind is TaskKind.PACKAGES_INSTALL),
            None,
        )

        self._wire_firewall(graph, firewall_task, install_task, server_task)
        self._wire_users(graph, user_tasks, firewall_task)
        self._wire_services(graph, service_tasks, firewall_task)
        self._wire_files(graph, file_tasks, service_tasks)
        self._wire_proxy(graph, proxy_task, install_task, firewall_task)

        graph.link_declared_dependencies()
        return Plan(graph, self.resolver)

    def _make_server_task(self, config: Config) -> Task | None:
        if config.server is None:
            return None
        params: dict[str, object] = {}
        if config.server.hostname:
            params["hostname"] = config.server.hostname
        if config.server.timezone:
            params["timezone"] = config.server.timezone
        if config.server.locale:
            params["locale"] = config.server.locale
        if not params:
            return None
        return Task(
            kind=TaskKind.SERVER,
            name="configure_server",
            description="Configure base server settings",
            explain=(
                "Sets the hostname, timezone and locale of the server "
                "so that logs and scheduled tasks use consistent values."
            ),
            params=params,
            idempotent=True,
        )

    def _make_package_tasks(self, config: Config, server_task: Task | None) -> list[Task]:
        if config.packages is None:
            return []
        result: list[Task] = []
        deps = [server_task.id] if server_task else []

        if config.packages.install:
            result.append(
                Task(
                    kind=TaskKind.PACKAGES_INSTALL,
                    name="install_packages",
                    description=f"Install {len(config.packages.install)} package(s)",
                    explain=(
                        "Installs the programs you asked for using the system "
                        "package manager through Ansible."
                    ),
                    params={"packages": list(config.packages.install)},
                    depends_on=list(deps),
                    idempotent=True,
                )
            )

        if config.packages.remove:
            result.append(
                Task(
                    kind=TaskKind.PACKAGES_REMOVE,
                    name="remove_packages",
                    description=f"Remove {len(config.packages.remove)} package(s)",
                    explain="Removes the programs you asked 0sys to uninstall.",
                    params={"packages": list(config.packages.remove)},
                    depends_on=list(deps),
                    idempotent=True,
                )
            )

        return result

    def _make_firewall_task(self, config: Config) -> Task | None:
        if config.firewall is None:
            return None
        return Task(
            kind=TaskKind.FIREWALL,
            name="configure_firewall",
            description="Configure firewall rules",
            explain=(
                "Opens only the ports you allowed and blocks everything else, "
                "so random people on the internet cannot reach your services."
            ),
            params={
                "default": config.firewall.default,
                "allow": list(config.firewall.allow),
            },
            idempotent=True,
        )

    def _make_user_tasks(self, config: Config, server_task: Task | None) -> list[Task]:
        tasks: list[Task] = []
        base_deps = [server_task.id] if server_task else []
        for user in config.users:
            tasks.append(
                Task(
                    kind=TaskKind.USER,
                    name=f"user_{user.name}",
                    target=user.name,
                    description=f"Create user '{user.name}'",
                    explain=(
                        f"Creates the account '{user.name}', adds it to the "
                        f"requested groups and installs the SSH key if provided."
                    ),
                    params={
                        "name": user.name,
                        "groups": list(user.groups),
                        "ssh_key": user.ssh_key,
                        "shell": user.shell,
                        "sudo": user.sudo,
                    },
                    depends_on=list(base_deps),
                    idempotent=True,
                )
            )
        return tasks

    def _make_service_tasks(self, config: Config, package_tasks: list[Task]) -> list[Task]:
        tasks: list[Task] = []
        install_dep_ids = [
            task.id for task in package_tasks if task.kind is TaskKind.PACKAGES_INSTALL
        ]
        for name, service in config.services.items():
            tasks.append(
                Task(
                    kind=TaskKind.SERVICE,
                    name=f"service_{name}",
                    target=name,
                    description=f"Manage service '{name}'",
                    explain=(
                        f"Makes sure '{name}' is running and starts automatically "
                        f"after a reboot. If a config file is provided, it is "
                        f"uploaded before restarting the service."
                    ),
                    params={
                        "name": name,
                        "state": service.state,
                        "enabled": service.enabled,
                        "config_file": service.config_file,
                    },
                    depends_on=list(install_dep_ids),
                    idempotent=True,
                )
            )
        return tasks

    def _make_file_tasks(self, config: Config, service_tasks: list[Task]) -> list[Task]:
        tasks: list[Task] = []
        service_ids = [task.id for task in service_tasks]
        for entry in config.files:
            tasks.append(
                Task(
                    kind=TaskKind.FILE,
                    name=f"file_{entry.dest}",
                    target=entry.dest,
                    description=f"Upload file to {entry.dest}",
                    explain=(
                        f"Copies a file from your machine to '{entry.dest}' on "
                        f"the server and applies the owner, group and mode."
                    ),
                    params={
                        "src": entry.src,
                        "dest": entry.dest,
                        "owner": entry.owner,
                        "group": entry.group,
                        "mode": entry.mode,
                    },
                    depends_on=list(service_ids),
                    idempotent=True,
                )
            )
        return tasks

    def _make_proxy_task(self, config: Config) -> Task | None:
        if config.proxy is None or not config.proxy.enabled:
            return None

        params: dict[str, object] = {
            "port": config.proxy.port,
            "sni": config.proxy.sni,
            "max_connections": config.proxy.max_connections,
            "log_level": config.proxy.log_level,
            "version": config.proxy.version,
            "install_dir": config.proxy.install_dir,
            "runtime": config.proxy.runtime,
        }
        if config.proxy.commit_sha:
            params["commit_sha"] = config.proxy.commit_sha
        if config.proxy.ssh_keys:
            params["ssh_keys"] = list(config.proxy.ssh_keys)

        return Task(
            kind=TaskKind.PROXY,
            name="configure_proxy",
            description="Deploy 0TPE proxy server",
            explain=(
                "Builds and starts the 0TPE proxy in Docker. "
                "Traffic from clients looks like HTTPS to the fallback SNI. "
                "Use '0sys 0tpe client-config' to generate a client config file."
            ),
            params=params,
            idempotent=True,
            critical=True,
        )

    def _make_command_tasks(self, config: Config) -> list[Task]:
        tasks: list[Task] = []
        for entry in config.commands:
            tasks.append(
                Task(
                    kind=TaskKind.COMMAND,
                    name=f"command_{entry.name}",
                    target=entry.name,
                    description=entry.name,
                    explain=(
                        "Runs a raw shell command you provided. 0sys cannot check "
                        "whether it already ran, so it will execute on every apply."
                    ),
                    params={"run": entry.run, "when": entry.when},
                    idempotent=entry.when != "always",
                )
            )
        return tasks

    def _wire_firewall(
        self,
        graph: DependencyGraph,
        firewall_task: Task | None,
        install_task: Task | None,
        server_task: Task | None,
    ) -> None:
        if firewall_task is None:
            return
        if install_task is not None:
            graph.add_dependency(firewall_task.id, install_task.id)
        elif server_task is not None:
            graph.add_dependency(firewall_task.id, server_task.id)

    def _wire_users(
        self,
        graph: DependencyGraph,
        user_tasks: list[Task],
        firewall_task: Task | None,
    ) -> None:
        if not user_tasks or firewall_task is None:
            return
        for task in user_tasks:
            graph.add_dependency(task.id, firewall_task.id)

    def _wire_services(
        self,
        graph: DependencyGraph,
        service_tasks: list[Task],
        firewall_task: Task | None,
    ) -> None:
        if not service_tasks or firewall_task is None:
            return
        for task in service_tasks:
            graph.add_dependency(task.id, firewall_task.id)

    def _wire_files(
        self,
        graph: DependencyGraph,
        file_tasks: list[Task],
        service_tasks: list[Task],
    ) -> None:
        if not file_tasks or not service_tasks:
            return
        for task in file_tasks:
            for service in service_tasks:
                if service.target and service.target in task.name:
                    graph.add_dependency(task.id, service.id)

    def _wire_proxy(
        self,
        graph: DependencyGraph,
        proxy_task: Task | None,
        install_task: Task | None,
        firewall_task: Task | None,
    ) -> None:
        if proxy_task is None:
            return
        if install_task is not None:
            graph.add_dependency(proxy_task.id, install_task.id)
        elif firewall_task is not None:
            graph.add_dependency(proxy_task.id, firewall_task.id)


def build_plan(config: Config, forced_backend: str | None = None) -> Plan:
    resolver = BackendResolver(forced=forced_backend)
    return Planner(resolver).build(config)
