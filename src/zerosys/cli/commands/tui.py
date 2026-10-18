from __future__ import annotations

import typer

from zerosys.tui.app import run_tui


def tui_command() -> None:
    try:
        run_tui()
    except ImportError as exc:
        typer.echo("Textual is not installed. Run 'pip install textual'", err=True)
        raise typer.Exit(code=1) from exc
