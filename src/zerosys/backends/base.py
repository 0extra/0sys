from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zerosys.core.planner.task import Task, TaskResult, TaskStatus


class BackendContext:
    def __init__(
        self,
        target_host: str = "localhost",
        target_user: str | None = None,
        target_port: int = 22,
        ssh_key: str | None = None,
        work_dir: str | None = None,
        dry_run: bool = False,
        verbose: bool = False,
        strict_host_key: bool = False,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.target_host = target_host
        self.target_user = target_user
        self.target_port = target_port
        self.ssh_key = ssh_key
        self.work_dir = work_dir
        self.dry_run = dry_run
        self.verbose = verbose
        self.strict_host_key = strict_host_key
        self.extra: dict[str, Any] = extra or {}

    def as_connection_dict(self) -> dict[str, Any]:
        return {
            "host": self.target_host,
            "user": self.target_user,
            "port": self.target_port,
            "ssh_key": self.ssh_key,
        }


class Backend(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    def supports(self, task: Task) -> bool: ...

    @abstractmethod
    def run(self, task: Task, context: BackendContext) -> TaskResult: ...

    def check(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(status=task.status, changed=False)

    def can_rollback(self, task: Task) -> bool:
        return False

    def rollback(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(
            status=TaskStatus.SKIPPED,
            message=f"backend '{self.name}' does not support rollback",
            changed=False,
        )

    def explain(self, task: Task) -> str:
        return task.explain or self.description
