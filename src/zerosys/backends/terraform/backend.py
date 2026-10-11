from __future__ import annotations

from pathlib import Path

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.terraform.generator import TerraformError, TerraformGenerator
from zerosys.core.config.schema import Config
from zerosys.core.planner.task import Task, TaskResult, TaskStatus


class TerraformBackend(Backend):
    name = "terraform"
    description = "Generates Terraform HCL for creating infrastructure"

    def __init__(self) -> None:
        self.generator = TerraformGenerator()

    def can_rollback(self, task: Task) -> bool:
        return False

    def supports(self, task: Task) -> bool:
        return False

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(
            status=TaskStatus.SKIPPED,
            message="terraform is an offline backend; use generate() instead",
            changed=False,
        )

    def generate(self, config: Config) -> dict[str, str]:
        return self.generator.generate(config)

    def write(self, config: Config, target_dir: Path | str) -> list[Path]:
        directory = Path(target_dir).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        files = self.generate(config)
        written: list[Path] = []
        for name, content in files.items():
            path = directory / name
            path.write_text(content, encoding="utf-8")
            written.append(path)
        return written

    def validate(self, config: Config) -> list[str]:
        issues: list[str] = []
        if config.infrastructure is None:
            issues.append("no 'infrastructure' section in config")
            return issues
        try:
            self.generator.generate(config)
        except TerraformError as exc:
            issues.append(str(exc))
        return issues
