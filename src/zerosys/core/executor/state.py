from __future__ import annotations

from dataclasses import dataclass, field

from zerosys.core.planner.task import Task, TaskStatus


@dataclass
class ExecutionState:
    total: int = 0
    completed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    rolled_back: int = 0
    executed_tasks: list[Task] = field(default_factory=list)
    failed_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    rolled_back_tasks: list[Task] = field(default_factory=list)
    current_task: Task | None = None

    def register_success(self, task: Task) -> None:
        self.completed += 1
        self.successful += 1
        self.executed_tasks.append(task)

    def register_failure(self, task: Task) -> None:
        self.completed += 1
        self.failed += 1
        self.failed_tasks.append(task)

    def register_skip(self, task: Task) -> None:
        self.completed += 1
        self.skipped += 1
        self.skipped_tasks.append(task)

    def register_rollback(self, task: Task) -> None:
        self.rolled_back += 1
        self.rolled_back_tasks.append(task)

    def has_failures(self) -> bool:
        return self.failed > 0

    def final_status(self) -> TaskStatus:
        if self.failed > 0:
            return TaskStatus.FAILED
        if self.completed == 0:
            return TaskStatus.SKIPPED
        return TaskStatus.SUCCESS

    def summary(self) -> str:
        return f"{self.successful} ok, {self.failed} failed, {self.skipped} skipped of {self.total}"
