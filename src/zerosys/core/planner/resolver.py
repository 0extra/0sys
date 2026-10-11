from __future__ import annotations

from zerosys.core.planner.task import Task, TaskKind

BACKEND_ANSIBLE = "ansible"
BACKEND_SHELL = "shell"
BACKEND_CLOUDINIT = "cloudinit"
BACKEND_TERRAFORM = "terraform"
BACKEND_NIXOS = "nixos"

ANSIBLE_KINDS: frozenset[TaskKind] = frozenset(
    {
        TaskKind.SERVER,
        TaskKind.PACKAGES_INSTALL,
        TaskKind.PACKAGES_REMOVE,
        TaskKind.SERVICE,
        TaskKind.USER,
        TaskKind.FIREWALL,
        TaskKind.FILE,
        TaskKind.PROXY,
    }
)

SHELL_KINDS: frozenset[TaskKind] = frozenset({TaskKind.COMMAND})


class BackendResolver:
    def __init__(self, forced: str | None = None) -> None:
        self._forced = forced

    def resolve(self, task: Task) -> str:
        if task.backend is not None:
            return task.backend
        if self._forced is not None:
            return self._forced
        return self._default_for_kind(task.kind)

    def _default_for_kind(self, kind: TaskKind) -> str:
        if kind in ANSIBLE_KINDS:
            return BACKEND_ANSIBLE
        if kind in SHELL_KINDS:
            return BACKEND_SHELL
        return BACKEND_SHELL


def resolve_backend(task: Task, forced: str | None = None) -> str:
    return BackendResolver(forced=forced).resolve(task)


def supports_backend(kind: TaskKind, backend: str) -> bool:
    if backend == BACKEND_ANSIBLE:
        return kind in ANSIBLE_KINDS
    return backend == BACKEND_SHELL
