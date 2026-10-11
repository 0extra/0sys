from __future__ import annotations

import typer
from rich.console import Console
from rich.text import Text

from zerosys.cli.ui.theme import get_console
from zerosys.knowledge import KnowledgeError, all_categories, tips

app = typer.Typer(help="Show practical tips for common tasks")


@app.callback(invoke_without_command=True)
def run(
    category: str | None = typer.Argument(None, help="Category name, for example 'firewall'"),
    list_categories: bool = typer.Option(False, "--list", "-l", help="List available categories"),
) -> None:
    console: Console = get_console()

    try:
        categories = all_categories()
    except KnowledgeError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    if list_categories or category is None:
        console.print("[primary]Available categories:[/primary]")
        for name in categories:
            console.print(f"  [accent]{name}[/accent]")
        console.print("[hint]Run: 0sys tips firewall[/hint]")
        raise typer.Exit(code=0)

    if category not in categories:
        console.print(f"[error]Unknown category '{category}'.[/error]")
        console.print(f"[hint]Try one of: {', '.join(categories)}[/hint]")
        raise typer.Exit(code=1)

    try:
        items = tips(category)
    except KnowledgeError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    console.print(f"[primary]{category}[/primary]")
    for item in items:
        console.print(f"  [success]•[/success] {item}")
