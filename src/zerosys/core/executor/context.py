from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from zerosys.backends.base import BackendContext
from zerosys.core.planner.planner import Plan


@dataclass
class ExecutionOptions:
    dry_run: bool = False
    verbose: bool = False
    stop_on_failure: bool = True
    rollback_on_failure: bool = False
    parallel: bool = False
    max_workers: int = 4
    tags: list[str] = field(default_factory=list)
    state_path: Path | None = None
    config_path: Path | None = None
    config_hash: str | None = None


@dataclass
class ExecutionContext:
    plan: Plan
    backend_context: BackendContext
    options: ExecutionOptions = field(default_factory=ExecutionOptions)

    @property
    def dry_run(self) -> bool:
        return self.options.dry_run

    @property
    def verbose(self) -> bool:
        return self.options.verbose
