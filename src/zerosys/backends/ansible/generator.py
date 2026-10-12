from __future__ import annotations

from typing import Any

from zerosys.core.planner.task import Task, TaskKind

ANSIBLE_ROLE_BY_KIND: dict[TaskKind, str] = {
    TaskKind.SERVER: "base",
    TaskKind.PACKAGES_INSTALL: "packages",
    TaskKind.PACKAGES_REMOVE: "packages",
    TaskKind.SERVICE: "service",
    TaskKind.USER: "users",
    TaskKind.FIREWALL: "firewall",
    TaskKind.FILE: "file",
    TaskKind.PROXY: "0tpe",
}


class PlaybookGenerator:
    def __init__(self, roles_dir: str = "roles") -> None:
        self.roles_dir = roles_dir

    def build_play(self, tasks: list[Task], host_pattern: str = "all") -> dict[str, Any]:
        return {
            "name": "0sys generated playbook",
            "hosts": host_pattern,
            "gather_facts": True,
            "become": True,
            "tasks": [self._task_to_play_entry(task) for task in tasks],
        }

    def build_playbook(self, tasks: list[Task], host_pattern: str = "all") -> list[dict[str, Any]]:
        return [self.build_play(tasks, host_pattern=host_pattern)]

    def build_rollback_playbook(
        self,
        tasks: list[Task],
        host_pattern: str = "all",
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for task in reversed(tasks):
            entry = self._task_to_rollback_entry(task)
            if entry is not None:
                entries.append(entry)
        if not entries:
            return []
        return [
            {
                "name": "0sys rollback playbook",
                "hosts": host_pattern,
                "gather_facts": False,
                "become": True,
                "tasks": entries,
            }
        ]

    def _task_to_rollback_entry(self, task: Task) -> dict[str, Any] | None:
        if task.kind is TaskKind.FILE:
            return self._rollback_file(task)
        if task.kind is TaskKind.USER:
            return self._rollback_user(task)
        if task.kind is TaskKind.SERVICE:
            return self._rollback_service(task)
        if task.kind is TaskKind.PACKAGES_INSTALL:
            return self._rollback_packages(task)
        return None

    def _rollback_file(self, task: Task) -> dict[str, Any]:
        dest = task.params.get("dest")
        return {
            "name": f"Remove file {dest}",
            "ansible.builtin.file": {
                "path": dest,
                "state": "absent",
            },
            "tags": ["rollback", task.kind.value],
        }

    def _rollback_user(self, task: Task) -> dict[str, Any]:
        name = task.params.get("name")
        return {
            "name": f"Remove user {name}",
            "ansible.builtin.user": {
                "name": name,
                "state": "absent",
                "remove": True,
            },
            "tags": ["rollback", task.kind.value],
        }

    def _rollback_service(self, task: Task) -> dict[str, Any]:
        name = task.params.get("name")
        return {
            "name": f"Stop service {name}",
            "ansible.builtin.service": {
                "name": name,
                "state": "stopped",
            },
            "tags": ["rollback", task.kind.value],
        }

    def _rollback_packages(self, task: Task) -> dict[str, Any]:
        packages = task.params.get("packages", [])
        return {
            "name": f"Remove packages {packages}",
            "ansible.builtin.package": {
                "name": packages,
                "state": "absent",
            },
            "tags": ["rollback", task.kind.value],
        }

    def _task_to_play_entry(self, task: Task) -> dict[str, Any]:
        role_name = self._role_for(task)
        if role_name is not None:
            return self._task_to_role_entry(task, role_name)
        return self._task_to_inline_entry(task)

    def _role_for(self, task: Task) -> str | None:
        if task.kind is TaskKind.PACKAGES_REMOVE:
            return None
        return ANSIBLE_ROLE_BY_KIND.get(task.kind)

    def _task_to_role_entry(self, task: Task, role_name: str) -> dict[str, Any]:
        return {
            "name": task.description or task.name,
            "role": role_name,
            "vars": self._role_vars(task, role_name),
            "tags": [task.kind.value, *task.tags],
        }

    def _role_vars(self, task: Task, role_name: str) -> dict[str, Any]:
        if role_name == "base":
            return {
                "server_hostname": task.params.get("hostname"),
                "server_timezone": task.params.get("timezone"),
                "server_locale": task.params.get("locale"),
            }
        if role_name == "packages":
            return {"packages_install": task.params.get("packages", [])}
        if role_name == "service":
            return {
                "service_name": task.params.get("name"),
                "service_state": task.params.get("state", "started"),
                "service_enabled": task.params.get("enabled", True),
                "service_config_file": task.params.get("config_file"),
            }
        if role_name == "users":
            return {
                "user_name": task.params.get("name"),
                "user_groups": task.params.get("groups", []),
                "user_ssh_key": task.params.get("ssh_key"),
                "user_shell": task.params.get("shell", "/bin/bash"),
                "user_sudo": task.params.get("sudo", False),
            }
        if role_name == "firewall":
            return {
                "firewall_default": task.params.get("default", "deny"),
                "firewall_allow": task.params.get("allow", []),
            }
        if role_name == "file":
            return {
                "file_src": task.params.get("src"),
                "file_dest": task.params.get("dest"),
                "file_owner": task.params.get("owner", "root"),
                "file_group": task.params.get("group", "root"),
                "file_mode": task.params.get("mode", "0644"),
            }
        if role_name == "0tpe":
            return {
                "proxy_port": task.params.get("port", 8443),
                "proxy_sni": task.params.get("sni", "www.microsoft.com"),
                "proxy_max_connections": task.params.get("max_connections", 512),
                "proxy_log_level": task.params.get("log_level", "info"),
                "proxy_version": task.params.get("version", "0.1.5"),
                "proxy_commit_sha": task.params.get("commit_sha", ""),
                "proxy_install_dir": task.params.get("install_dir", "/opt/0tpe"),
            }
        return {}

    def _task_to_inline_entry(self, task: Task) -> dict[str, Any]:
        if task.kind is TaskKind.PACKAGES_REMOVE:
            return {
                "name": task.description or task.name,
                "ansible.builtin.package": {
                    "name": task.params.get("packages", []),
                    "state": "absent",
                },
                "tags": [task.kind.value, *task.tags],
            }
        return {
            "name": task.description or task.name,
            "ansible.builtin.debug": {"msg": f"no role mapping for kind {task.kind.value}"},
        }
