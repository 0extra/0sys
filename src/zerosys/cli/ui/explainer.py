from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from zerosys.core.planner.task import Task, TaskStatus

TASK_KIND_LABELS: dict[str, str] = {
    "server": "Server basics",
    "packages.install": "Install packages",
    "packages.remove": "Remove packages",
    "service": "Manage service",
    "user": "Create user",
    "firewall": "Firewall",
    "file": "Upload file",
    "command": "Run command",
    "proxy": "Deploy 0TPE proxy",
}


def kind_label(kind_value: str) -> str:
    return TASK_KIND_LABELS.get(kind_value, kind_value)


def explain_task(task: Task, console: Console) -> None:
    if not task.explain:
        return
    title = f"[task.kind]{kind_label(task.kind.value)}[/task.kind]"
    if task.target:
        title += f" [task.target]{task.target}[/task.target]"
    console.print(
        Panel(
            Text(task.explain),
            title=title,
            border_style="info",
            padding=(0, 2),
        )
    )


def print_task_start(task: Task, console: Console) -> None:
    label = kind_label(task.kind.value)
    target = f" [task.target]{task.target}[/task.target]" if task.target else ""
    console.print(f"[primary]→[/primary] {label}{target} [muted]...[/muted]")


def print_task_finish(task: Task, console: Console) -> None:
    label = kind_label(task.kind.value)
    target = f" [task.target]{task.target}[/task.target]" if task.target else ""
    status = task.status

    if status is TaskStatus.SUCCESS:
        changed = task.result.changed if task.result else False
        suffix = " [muted](changed)[/muted]" if changed else " [muted](no change)[/muted]"
        console.print(f"[task.success]✓[/task.success] {label}{target}{suffix}")
        if task.result and task.result.message.startswith("[dry-run]"):
            console.print(Text(f"  {task.result.message}", style="hint"))
    elif status is TaskStatus.SKIPPED:
        reason = task.result.message if task.result else ""
        console.print(f"[task.skip]•[/task.skip] {label}{target} [muted]{reason}[/muted]")
    elif status is TaskStatus.FAILED:
        message = task.result.message if task.result else ""
        console.print(f"[task.failure]✗[/task.failure] {label}{target} [muted]{message}[/muted]")
    elif status is TaskStatus.ROLLED_BACK:
        console.print(f"[task.rollback]↺[/task.rollback] {label}{target}")
    else:
        console.print(f"[muted]? {label}{target}[/muted]")


def print_task_error(task: Task, console: Console) -> None:
    if task.result is None:
        return
    if task.result.stderr:
        console.print(
            Panel(
                Text(task.result.stderr.rstrip()),
                title="stderr",
                border_style="error",
            )
        )
    elif task.result.stdout:
        console.print(
            Panel(
                Text(task.result.stdout.rstrip()),
                title="stdout",
                border_style="error",
            )
        )


def print_hint(text: str, console: Console) -> None:
    console.print(Text(text, style="hint"))


def print_success(text: str, console: Console) -> None:
    console.print(Text(text, style="success"))


def print_warning(text: str, console: Console) -> None:
    console.print(Text(text, style="warning"))


def print_error(text: str, console: Console) -> None:
    console.print(Text(text, style="error"))
