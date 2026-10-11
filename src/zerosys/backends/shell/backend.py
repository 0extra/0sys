from __future__ import annotations

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.shell.runner import run_local, run_remote
from zerosys.core.errors import BackendError
from zerosys.core.planner.task import Task, TaskKind, TaskResult, TaskStatus


class ShellBackend(Backend):
    name = "shell"
    description = "Runs raw shell commands on the target host"

    def supports(self, task: Task) -> bool:
        return task.kind is TaskKind.COMMAND

    def can_rollback(self, task: Task) -> bool:
        return False

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        if not self.supports(task):
            raise BackendError(f"shell backend does not support task kind '{task.kind.value}'")

        command = task.params.get("run")
        if not command:
            raise BackendError(f"task '{task.name}' has no 'run' parameter")

        if context.dry_run:
            return TaskResult(
                status=TaskStatus.SUCCESS,
                message=f"[dry-run] would run: {command}",
                changed=False,
            )

        if context.target_host in {"localhost", "127.0.0.1", "::1"}:
            result = run_local(command)
        else:
            result = run_remote(
                command=command,
                host=context.target_host,
                user=context.target_user,
                port=context.target_port,
                ssh_key=context.ssh_key,
            )

        if result.success:
            return TaskResult(
                status=TaskStatus.SUCCESS,
                message=f"executed in {result.duration_ms} ms",
                stdout=result.stdout,
                stderr=result.stderr,
                changed=True,
                duration_ms=result.duration_ms,
            )

        return TaskResult(
            status=TaskStatus.FAILED,
            message=f"exit code {result.exit_code}",
            stdout=result.stdout,
            stderr=result.stderr,
            changed=True,
            duration_ms=result.duration_ms,
        )

    def check(self, task: Task, context: BackendContext) -> TaskResult:
        if not self.supports(task):
            return TaskResult(status=TaskStatus.SKIPPED)
        return TaskResult(
            status=TaskStatus.SUCCESS,
            message="shell commands are not idempotent and cannot be checked",
            changed=False,
        )
