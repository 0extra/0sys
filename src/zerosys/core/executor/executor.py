from __future__ import annotations

from collections.abc import Callable

from zerosys.backends.base import Backend
from zerosys.backends.registry import get_backend, load_default_backends
from zerosys.core.errors import BackendError, ExecutorError
from zerosys.core.executor.context import ExecutionContext
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.task import Task, TaskResult, TaskStatus

ProgressCallback = Callable[[Task], None]


class Executor:
    def __init__(
        self,
        context: ExecutionContext,
        on_task_start: ProgressCallback | None = None,
        on_task_finish: ProgressCallback | None = None,
    ) -> None:
        self.context = context
        self.state = ExecutionState(total=context.plan.size())
        self.on_task_start = on_task_start
        self.on_task_finish = on_task_finish
        load_default_backends()

    def execute(self) -> ExecutionState:
        failed = False
        for level in self.context.plan.levels():
            for task in level:
                if failed:
                    task.mark_skipped("previous task failed")
                    self.state.register_skip(task)
                    self._notify_finish(task)
                    continue

                if not self._matches_tags(task):
                    task.mark_skipped("tag filter")
                    self.state.register_skip(task)
                    self._notify_finish(task)
                    continue

                self._execute_task(task)

                if task.status is TaskStatus.FAILED and self.context.options.stop_on_failure:
                    failed = True

        return self.state

    def _execute_task(self, task: Task) -> None:
        self.state.current_task = task
        self._notify_start(task)

        backend = self._resolve_backend(task)

        try:
            task.mark_running()
            result = backend.run(task, self.context.backend_context)
        except BackendError as exc:
            result = TaskResult(
                status=TaskStatus.FAILED,
                message=str(exc),
                changed=False,
            )
        except Exception as exc:
            result = TaskResult(
                status=TaskStatus.FAILED,
                message=f"unexpected error: {exc}",
                changed=False,
            )

        if result.status is TaskStatus.SUCCESS:
            task.mark_success(result)
            self.state.register_success(task)
        elif result.status is TaskStatus.SKIPPED:
            task.mark_skipped(result.message)
            self.state.register_skip(task)
        else:
            task.mark_failed(result)
            self.state.register_failure(task)

        self._notify_finish(task)

    def _resolve_backend(self, task: Task) -> Backend:
        if task.backend is None:
            raise ExecutorError(f"task '{task.name}' has no backend assigned")
        try:
            return get_backend(task.backend)
        except BackendError as exc:
            raise ExecutorError(str(exc)) from exc

    def _matches_tags(self, task: Task) -> bool:
        requested = self.context.options.tags
        if not requested:
            return True
        if not task.tags:
            return False
        return bool(set(requested) & set(task.tags))

    def _notify_start(self, task: Task) -> None:
        if self.on_task_start is not None:
            self.on_task_start(task)

    def _notify_finish(self, task: Task) -> None:
        if self.on_task_finish is not None:
            self.on_task_finish(task)
