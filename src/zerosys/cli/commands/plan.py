from __future__ import annotations

from pathlib import Path

import typer
from rich.text import Text
from rich.tree import Tree

from zerosys.cli.ui.explainer import kind_label
from zerosys.cli.ui.theme import get_console
from zerosys.core.config import load_config, validate
from zerosys.core.errors import ConfigError, PlannerError
from zerosys.core.planner import build_plan
from zerosys.core.planner.task import Task

app = typer.Typer(help="Show what 0sys would do without changing anything")


def _print_task_tree(task: Task, tree: Tree) -> None:
    label = kind_label(task.kind.value)
    header = Text()
    header.append(label, style="task.kind")
    if task.target:
        header.append(f" {task.target}", style="task.target")
    if task.backend:
        header.append(f" ({task.backend})", style="accent")
    node = tree.add(header)
    if task.explain:
        node.add(Text(task.explain, style="hint"))


@app.callback(invoke_without_command=True)
def run(
    config: Path = typer.Argument(..., exists=True, readable=True, help="Path to config file"),
    backend: str | None = typer.Option(None, "--backend", help="Force a specific backend"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags filter"),
) -> None:
    console = get_console()
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    report = validate(cfg)
    for issue in report.issues:
        style = {
            "error": "error",
            "warning": "warning",
            "info": "info",
        }.get(issue.severity.value, "muted")
        console.print(Text(str(issue), style=style))

    if report.has_errors:
        console.print("[error]Config has errors, plan aborted.[/error]")
        raise typer.Exit(code=2)

    try:
        plan = build_plan(cfg, forced_backend=backend)
    except PlannerError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    tree = Tree("[primary]Execution plan[/primary]")
    for level_index, level in enumerate(plan.levels(), start=1):
        level_node = tree.add(f"[info]Level {level_index}[/info]")
        for task in level:
            _print_task_tree(task, level_node)

    console.print(tree)

    summary = plan.summary()
    console.print(
        "[muted]Backends:[/muted] "
        + ", ".join(f"{name}={count}" for name, count in sorted(summary.items()))
    )
    console.print(f"[muted]Total tasks:[/muted] {plan.size()}")

    if tags:
        console.print(f"[muted]Tags filter:[/muted] {tags}")
