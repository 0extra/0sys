from __future__ import annotations

import shutil
from pathlib import Path

from zerosys.backends.ansible.generator import PlaybookGenerator
from zerosys.backends.ansible.runner import AnsibleRunner
from zerosys.backends.base import Backend, BackendContext
from zerosys.core.errors import BackendError
from zerosys.core.planner.resolver import ANSIBLE_KINDS
from zerosys.core.planner.task import Task, TaskKind, TaskResult, TaskStatus

ROLLBACK_KINDS: frozenset[TaskKind] = frozenset(
    {
        TaskKind.FILE,
        TaskKind.USER,
        TaskKind.SERVICE,
        TaskKind.PACKAGES_INSTALL,
    }
)


class AnsibleBackend(Backend):
    name = "ansible"
    description = "Runs configuration tasks through Ansible over SSH"

    def __init__(self, roles_path: Path | None = None) -> None:
        self.roles_path = roles_path or self._default_roles_path()
        self.generator = PlaybookGenerator()

    def _default_roles_path(self) -> Path:
        return Path(__file__).resolve().parent / "roles"

    def supports(self, task: Task) -> bool:
        return task.kind in ANSIBLE_KINDS

    def can_rollback(self, task: Task) -> bool:
        return task.kind in ROLLBACK_KINDS

    def _ensure_ansible(self) -> None:
        if shutil.which("ansible-playbook") is None:
            raise BackendError(
                "ansible-playbook was not found in PATH. "
                "Install Ansible with 'pacman -S ansible' or 'pip install ansible-core'."
            )

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        if not self.supports(task):
            raise BackendError(f"ansible backend does not support task kind '{task.kind.value}'")

        if context.dry_run:
            return TaskResult(
                status=TaskStatus.SUCCESS,
                message=f"[dry-run] would run {task.kind.value} via ansible",
                changed=False,
            )

        self._ensure_ansible()

        playbook = self.generator.build_playbook([task])
        runner = self._build_runner(context)
        result = runner.run(playbook, tags=[task.kind.value])
        return self._convert_result(result)

    def rollback(self, task: Task, context: BackendContext) -> TaskResult:
        if not self.can_rollback(task):
            return TaskResult(
                status=TaskStatus.SKIPPED,
                message=f"task kind '{task.kind.value}' is not reversible",
                changed=False,
            )

        if context.dry_run:
            return TaskResult(
                status=TaskStatus.SUCCESS,
                message=f"[dry-run] would roll back {task.kind.value}",
                changed=False,
            )

        self._ensure_ansible()

        playbook = self.generator.build_rollback_playbook([task])
        if not playbook:
            return TaskResult(
                status=TaskStatus.SKIPPED,
                message="no rollback playbook generated",
                changed=False,
            )

        runner = self._build_runner(context)
        result = runner.run(playbook, tags=["rollback"])
        return self._convert_result(result)

    def _build_runner(self, context: BackendContext) -> AnsibleRunner:
        return AnsibleRunner(
            inventory_host=context.target_host,
            inventory_user=context.target_user,
            inventory_port=context.target_port,
            ssh_key=context.ssh_key,
            roles_path=self.roles_path,
            verbose=context.verbose,
        )

    def _convert_result(self, result: object) -> TaskResult:
        success = bool(getattr(result, "success", False))
        status_text = str(getattr(result, "status", "unknown"))
        stdout = str(getattr(result, "stdout", ""))
        stderr = str(getattr(result, "stderr", ""))
        stats = getattr(result, "stats", {}) or {}
        duration_ms = int(getattr(result, "duration_ms", 0))

        if success:
            return TaskResult(
                status=TaskStatus.SUCCESS,
                message=f"ansible run {status_text}",
                stdout=stdout,
                stderr=stderr,
                changed=self._was_changed(stats),
                duration_ms=duration_ms,
            )

        return TaskResult(
            status=TaskStatus.FAILED,
            message=f"ansible run {status_text}",
            stdout=stdout,
            stderr=stderr,
            changed=False,
            duration_ms=duration_ms,
        )

    def _was_changed(self, stats: dict[str, object]) -> bool:
        if not stats:
            return True
        for host_stats in stats.values():
            if not isinstance(host_stats, dict):
                continue
            changed = host_stats.get("changed", 0)
            if isinstance(changed, int) and changed > 0:
                return True
        return False

    def check(self, task: Task, context: BackendContext) -> TaskResult:
        if not self.supports(task):
            return TaskResult(status=TaskStatus.SKIPPED)

        self._ensure_ansible()

        playbook = self.generator.build_playbook([task])
        runner = self._build_runner(context)
        result = runner.run(playbook, tags=[task.kind.value], check=True)

        return TaskResult(
            status=TaskStatus.SUCCESS if result.success else TaskStatus.FAILED,
            message="ansible check mode",
            stdout=result.stdout,
            stderr=result.stderr,
            changed=False,
        )
