from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from zerosys.cli.ui.theme import get_console
from zerosys.knowledge import (
    KnowledgeError,
    all_terms,
    lookup,
)

app = typer.Typer(help="Explain a technical term in plain English")


@app.callback(invoke_without_command=True)
def run(
    term: str | None = typer.Argument(None, help="Term to explain, for example 'ufw'"),
    list_terms: bool = typer.Option(False, "--list", "-l", help="List all known terms"),
) -> None:
    console: Console = get_console()

    if list_terms or term is None:
        _print_glossary(console)
        raise typer.Exit(code=0)

    try:
        entry = lookup(term)
    except KnowledgeError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    if entry is None:
        console.print(f"[error]No explanation for '{term}'.[/error]")
        console.print("[hint]Run '0sys explain-term --list' to see what is available.[/hint]")
        raise typer.Exit(code=1)

    body = Text()
    body.append(f"{entry.term}\n\n", style="bold primary")
    body.append(f"{entry.simple}\n\n")
    if entry.why:
        body.append("Why it matters\n", style="accent")
        body.append(f"{entry.why}\n\n")
    if entry.example:
        body.append("Example\n", style="accent")
        body.append(f"{entry.example}\n")

    console.print(Panel(body, border_style="info", padding=(1, 2)))


def _print_glossary(console: Console) -> None:
    try:
        terms = all_terms()
    except KnowledgeError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    table = Table(title="Glossary", border_style="primary")
    table.add_column("Term", style="accent")
    table.add_column("Meaning", style="white")

    for entry in terms:
        table.add_row(entry.key, entry.simple)

    console.print(table)
    console.print("[hint]Run: 0sys explain-term ufw[/hint]")
