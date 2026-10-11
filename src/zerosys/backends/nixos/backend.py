from __future__ import annotations

from pathlib import Path

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.nixos.generator import NixosGenerator
from zerosys.core.config.schema import Config
from zerosys.core.planner.task import Task, TaskResult, TaskStatus


class NixosBackend(Backend):
    name = "nixos"
    description = "Generates a NixOS configuration.nix from the config"

    def __init__(self) -> None:
        self.generator = NixosGenerator()

    def supports(self, task: Task) -> bool:
        return False

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(
            status=TaskStatus.SKIPPED,
            message="nixos is an offline backend; use generate() instead",
            changed=False,
        )

    def generate(self, config: Config) -> str:
        return self.generator.generate(config)

    def write(self, config: Config, path: Path | str) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.generate(config), encoding="utf-8")
        return target
