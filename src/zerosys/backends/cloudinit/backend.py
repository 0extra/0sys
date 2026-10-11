from __future__ import annotations

from pathlib import Path

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.cloudinit.generator import CloudInitGenerator
from zerosys.core.config.schema import Config
from zerosys.core.planner.task import Task, TaskResult, TaskStatus


class CloudInitBackend(Backend):
    name = "cloudinit"
    description = "Generates cloud-init user-data for VPS providers"

    def __init__(self) -> None:
        self.generator = CloudInitGenerator()

    def supports(self, task: Task) -> bool:
        return False

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(
            status=TaskStatus.SKIPPED,
            message="cloud-init is an offline backend; use generate() instead",
            changed=False,
        )

    def generate(self, config: Config) -> str:
        return self.generator.generate(config)

    def write(self, config: Config, path: Path | str) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.generate(config), encoding="utf-8")
        return target
