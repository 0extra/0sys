from __future__ import annotations

from dataclasses import dataclass, field

from zerosys.backends.base import Backend
from zerosys.backends.registry import get_backend
from zerosys.core.errors import RollbackError
from zerosys.core.executor.context import ExecutionContext
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.task import Task, TaskKind, TaskResult, TaskStatus

HELD_WITHOUT_AGGRESSIVE: frozenset[TaskKind] = frozenset({TaskKind.PACKAGES_INSTALL, TaskKind.USER})


@dataclass
class RollbackOptions:
    aggressive: bool = False
    stop_on_failure: bool = True


@dataclass
class RollbackReport:
    attempted: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    not_reversible: list[str] = field(default_factory=list)
    reversed_tasks: list[Task] = field(default_factory=list)
    failed_tasks: list[Task] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"{self.successful} rolled back, {self.failed} failed, "
            f"{self.skipped} skipped, {len(self.not_reversible)} not reversible"
        )


class Rollbacker:
    def __init__(
        self,
        context: ExecutionContext,
        state: ExecutionState,
        options: RollbackOptions | None = None,
    ) -> None:
        self.context = context
        self.state = state
        self.options = options or RollbackOptions()

    def rollback(self) -> RollbackReport:
        report = RollbackReport()
        ordered = list(reversed(self.state.executed_tasks))

        for task in ordered:
            if not task.idempotent:
                continue

            if task.result is not None and not task.result.changed:
                if not self.options.aggressive:
                    report.skipped += 1
                    continue
                if task.kind not in HELD_WITHOUT_AGGRESSIVE:
                    report.skipped += 1
                    continue

            backend = self._backend_for(task)
            if backend is None:
                report.not_reversible.append(task.name)
                continue
            if not backend.can_rollback(task):
                report.not_reversible.append(task.name)
                continue
            if task.kind in HELD_WITHOUT_AGGRESSIVE and not self.options.aggressive:
                report.not_reversible.append(task.name)
                continue

            report.attempted += 1
            result = self._attempt_rollback(task, backend)
            if result.status is TaskStatus.SUCCESS:
                report.successful += 1
                report.reversed_tasks.append(task)
                task.mark_rolled_back(result.message)
                self.state.register_rollback(task)
            elif result.status is TaskStatus.SKIPPED:
                report.skipped += 1
            else:
                report.failed += 1
                report.failed_tasks.append(task)
                task.mark_failed(result)
                if self.options.stop_on_failure:
                    break

        return report

    def _backend_for(self, task: Task) -> Backend | None:
        if task.backend is None:
            return None
        try:
            return get_backend(task.backend)
        except Exception:
            return None

    def _attempt_rollback(self, task: Task, backend: Backend) -> TaskResult:
        try:
            return backend.rollback(task, self.context.backend_context)
        except Exception as exc:
            raise RollbackError(f"rollback failed for '{task.name}': {exc}") from exc


def rollback(
    context: ExecutionContext,
    state: ExecutionState,
    options: RollbackOptions | None = None,
) -> RollbackReport:
    return Rollbacker(context, state, options).rollback()
