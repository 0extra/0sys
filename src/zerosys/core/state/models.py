from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from zerosys.core.planner.task import TaskKind, TaskResult, TaskStatus
from zerosys.core.security.secrets import redact_dict, redact_text


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


def _now() -> str:
    return datetime.now(UTC).isoformat()


class RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    config_path: str | None = None
    config_hash: str | None = None
    target_host: str = "localhost"
    target_user: str | None = None
    target_port: int = 22
    ssh_key_path: str | None = None
    started_at: str = Field(default_factory=_now)
    finished_at: str | None = None
    status: TaskStatus = TaskStatus.RUNNING
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    dry_run: bool = False

    def finish(self, status: TaskStatus) -> None:
        self.status = status
        self.finished_at = _now()

    def to_row(self) -> tuple[Any, ...]:
        return (
            self.id,
            self.config_path,
            self.config_hash,
            self.target_host,
            self.target_user,
            self.target_port,
            self.ssh_key_path,
            self.started_at,
            self.finished_at,
            self.status.value,
            self.total_tasks,
            self.successful_tasks,
            self.failed_tasks,
            self.skipped_tasks,
            int(self.dry_run),
        )

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> RunRecord:
        return cls(
            id=row[0],
            config_path=row[1],
            config_hash=row[2],
            target_host=row[3],
            target_user=row[4],
            target_port=row[5] if row[5] is not None else 22,
            ssh_key_path=row[6],
            started_at=row[7],
            finished_at=row[8],
            status=TaskStatus(row[9]),
            total_tasks=row[10],
            successful_tasks=row[11],
            failed_tasks=row[12],
            skipped_tasks=row[13],
            dry_run=bool(row[14]),
        )


class TaskRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    run_id: str
    task_id: str
    kind: TaskKind
    name: str
    target: str | None = None
    backend: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    message: str = ""
    stdout: str = ""
    stderr: str = ""
    changed: bool = False
    duration_ms: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)

    def to_row(self) -> tuple[Any, ...]:
        return (
            self.id,
            self.run_id,
            self.task_id,
            self.kind.value,
            self.name,
            self.target,
            self.backend,
            self.status.value,
            self.message,
            self.stdout,
            self.stderr,
            int(self.changed),
            self.duration_ms,
            self.started_at,
            self.finished_at,
            json.dumps(self.params, default=str),
        )

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> TaskRecord:
        params_raw = row[15]
        params: dict[str, Any] = {}
        if params_raw:
            try:
                loaded = json.loads(params_raw)
                if isinstance(loaded, dict):
                    params = loaded
            except json.JSONDecodeError:
                params = {}
        return cls(
            id=row[0],
            run_id=row[1],
            task_id=row[2],
            kind=TaskKind(row[3]),
            name=row[4],
            target=row[5],
            backend=row[6],
            status=TaskStatus(row[7]),
            message=row[8] or "",
            stdout=row[9] or "",
            stderr=row[10] or "",
            changed=bool(row[11]),
            duration_ms=row[12] or 0,
            started_at=row[13],
            finished_at=row[14],
            params=params,
        )

    @classmethod
    def from_task(cls, run_id: str, task: Any) -> TaskRecord:
        result: TaskResult | None = task.result
        return cls(
            run_id=run_id,
            task_id=task.id,
            kind=task.kind,
            name=task.name,
            target=task.target,
            backend=task.backend,
            status=task.status,
            message=redact_text(result.message) if result else "",
            stdout=redact_text(result.stdout) if result else "",
            stderr=redact_text(result.stderr) if result else "",
            changed=result.changed if result else False,
            duration_ms=result.duration_ms if result else 0,
            started_at=task.started_at.isoformat() if task.started_at else None,
            finished_at=task.finished_at.isoformat() if task.finished_at else None,
            params=redact_dict(dict(task.params)),
        )
