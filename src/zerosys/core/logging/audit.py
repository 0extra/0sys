from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from platformdirs import user_data_dir

DEFAULT_AUDIT_DIR = Path(user_data_dir("0sys", "0extra")) / "audit"


@dataclass
class AuditEvent:
    timestamp: str
    action: str
    target: str = ""
    run_id: str = ""
    task_name: str = ""
    status: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        return cls(
            timestamp=str(data.get("timestamp", "")),
            action=str(data.get("action", "")),
            target=str(data.get("target", "")),
            run_id=str(data.get("run_id", "")),
            task_name=str(data.get("task_name", "")),
            status=str(data.get("status", "")),
            details=dict(data.get("details", {})),
        )


class AuditLog:
    def __init__(self, path: Path | None = None, run_id: str = "") -> None:
        self.run_id = run_id
        self.path = path or self._default_path(run_id)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _default_path(self, run_id: str) -> Path:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        identifier = run_id or "run"
        return DEFAULT_AUDIT_DIR / f"{stamp}-{identifier}.jsonl"

    def record(
        self,
        action: str,
        target: str = "",
        task_name: str = "",
        status: str = "",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            timestamp=datetime.now(UTC).isoformat(),
            action=action,
            target=target,
            run_id=self.run_id,
            task_name=task_name,
            status=status,
            details=details or {},
        )
        self._append(event)
        return event

    def _append(self, event: AuditEvent) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json())
            handle.write("\n")

    def read(self, limit: int = 0) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        events: list[AuditEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    events.append(AuditEvent.from_dict(data))
        if limit > 0:
            return events[-limit:]
        return events

    def count(self) -> int:
        return len(self.read())


def list_audit_logs() -> list[Path]:
    if not DEFAULT_AUDIT_DIR.exists():
        return []
    return sorted(DEFAULT_AUDIT_DIR.glob("*.jsonl"), reverse=True)


def latest_audit_log() -> Path | None:
    logs = list_audit_logs()
    return logs[0] if logs else None
