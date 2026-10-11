from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

from zerosys.core.planner.task import Task


@dataclass
class ProgressReporter:
    console: Console
    total: int
    description: str = "Applying plan"
    _progress: Progress | None = field(default=None, init=False)
    _task_id: TaskID | None = field(default=None, init=False)

    def start(self) -> None:
        self._progress = Progress(
            SpinnerColumn(style="primary"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, style="primary", complete_style="success"),
            TextColumn("[muted]{task.completed}/{task.total}[/muted]"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(self.description, total=self.total)

    def advance(self, task: Task) -> None:
        if self._progress is None or self._task_id is None:
            return
        self._progress.update(
            self._task_id,
            advance=1,
            description=f"{self.description} [muted]{task.name}[/muted]",
        )

    def stop(self) -> None:
        if self._progress is not None:
            self._progress.stop()
            self._progress = None
            self._task_id = None


class NullReporter:
    def start(self) -> None:
        return None

    def advance(self, task: Task) -> None:
        return None

    def stop(self) -> None:
        return None
