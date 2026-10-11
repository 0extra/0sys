from __future__ import annotations

from zerosys.backends.registry import get_backend, load_default_backends
from zerosys.core.errors import RollbackError
from zerosys.core.executor.context import ExecutionContext
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.task import Task, TaskResult, TaskStatus


class Rollbacker:
    def __init__(self, context: ExecutionContext, state: ExecutionState) -> None:
        self.context = context
        self.state = state
        load_default_backends()

    def rollback(self) -> ExecutionState:
        ordered = list(reversed(self.state.executed_tasks))
        for task in ordered:
            if not task.idempotent:
                continue
            self._rollback_task(task)
        return self.state

    def _rollback_task(self, task: Task) -> None:
        if task.backend is None:
            raise RollbackError(f"task '{task.name}' has no backend assigned")
        backend = get_backend(task.backend)
        try:
            result = (
                backend.rollback(task, self.context.backend_context)
                if hasattr(backend, "rollback")
                else None
            )
        except Exception as exc:
            raise RollbackError(f"rollback failed for '{task.name}': {exc}") from exc

        if result is None:
            result = TaskResult(
                status=TaskStatus.ROLLED_BACK,
                message="no rollback available for this backend",
            )

        task.mark_rolled_back(result.message)
        self.state.register_rollback(task)


def rollback(context: ExecutionContext, state: ExecutionState) -> ExecutionState:
    return Rollbacker(context, state).rollback()
