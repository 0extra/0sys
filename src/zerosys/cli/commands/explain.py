from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.text import Text

from zerosys.cli.ui.explainer import kind_label
from zerosys.cli.ui.theme import get_console
from zerosys.core.config import load_config
from zerosys.core.errors import ConfigError, PlannerError
from zerosys.core.planner import build_plan

app = typer.Typer(help="Explain what a configuration will do in plain English")


@app.callback(invoke_without_command=True)
def run(
    config: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    console: Console = get_console()
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        console.print(f"[error]{exc}[/error]", markup=False)
        raise typer.Exit(code=1) from exc

    try:
        plan = build_plan(cfg)
    except PlannerError as exc:
        console.print(f"[error]{exc}[/error]", markup=False)
        raise typer.Exit(code=1) from exc

    console.print("[primary]What this config will do:[/primary]\n")

    for index, task in enumerate(plan.tasks(), start=1):
        label = kind_label(task.kind.value)
        header = Text()
        header.append(f"{index}. ", style="accent")
        header.append(label, style="bold")
        if task.target:
            header.append(f" {task.target}", style="task.target")
        console.print(header)
        if task.explain:
            console.print(Text(f"   {task.explain}", style="hint"))
        console.print()
