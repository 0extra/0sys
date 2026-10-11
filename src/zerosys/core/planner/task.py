from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskKind(StrEnum):
    SERVER = "server"
    PACKAGES_INSTALL = "packages.install"
    PACKAGES_REMOVE = "packages.remove"
    SERVICE = "service"
    USER = "user"
    FIREWALL = "firewall"
    FILE = "file"
    COMMAND = "command"
    PROXY = "proxy"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class TaskResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TaskStatus
    message: str = ""
    stdout: str = ""
    stderr: str = ""
    changed: bool = False
    duration_ms: int = 0


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    kind: TaskKind
    name: str
    target: str | None = None
    backend: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    explain: str = ""
    idempotent: bool = True
    critical: bool = True
    status: TaskStatus = TaskStatus.PENDING
    result: TaskResult | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def mark_success(self, result: TaskResult) -> None:
        self.status = TaskStatus.SUCCESS
        self.result = result
        self.finished_at = datetime.now(UTC)

    def mark_failed(self, result: TaskResult) -> None:
        self.status = TaskStatus.FAILED
        self.result = result
        self.finished_at = datetime.now(UTC)

    def mark_skipped(self, reason: str = "") -> None:
        self.status = TaskStatus.SKIPPED
        self.result = TaskResult(status=TaskStatus.SKIPPED, message=reason)
        self.finished_at = datetime.now(UTC)

    def mark_rolled_back(self, reason: str = "") -> None:
        self.status = TaskStatus.ROLLED_BACK
        self.result = TaskResult(status=TaskStatus.ROLLED_BACK, message=reason)
        self.finished_at = datetime.now(UTC)

    def duration_ms(self) -> int:
        if self.started_at is None or self.finished_at is None:
            return 0
        delta = self.finished_at - self.started_at
        return int(delta.total_seconds() * 1000)

    def short_label(self) -> str:
        if self.target:
            return f"{self.kind.value}:{self.target}"
        return f"{self.kind.value}:{self.name}"
