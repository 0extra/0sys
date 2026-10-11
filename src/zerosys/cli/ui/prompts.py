from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt


def ask_text(
    question: str,
    console: Console,
    default: str | None = None,
    password: bool = False,
) -> str:
    if default is not None:
        return Prompt.ask(
            question,
            console=console,
            default=default,
            password=password,
            show_default=True,
        )
    return Prompt.ask(
        question,
        console=console,
        password=password,
        show_default=False,
    )


def ask_int(
    question: str,
    console: Console,
    default: int | None = None,
) -> int:
    if default is not None:
        return IntPrompt.ask(
            question,
            console=console,
            default=default,
            show_default=True,
        )
    return IntPrompt.ask(question, console=console, show_default=False)


def ask_confirm(
    question: str,
    console: Console,
    default: bool = True,
) -> bool:
    return Confirm.ask(question, console=console, default=default)


def ask_choice(
    question: str,
    choices: list[str],
    console: Console,
    default: str | None = None,
) -> str:
    console.print(f"[primary]{question}[/primary]")
    for idx, choice in enumerate(choices, start=1):
        console.print(f"  [accent]{idx}[/accent]) {choice}")

    default_index: int | None = None
    if default is not None and default in choices:
        default_index = choices.index(default) + 1

    while True:
        if default_index is not None:
            raw = Prompt.ask("Choose", console=console, default=str(default_index))
        else:
            raw = Prompt.ask("Choose", console=console)
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(choices):
                return choices[index - 1]
        if raw in choices:
            return raw
        console.print("[error]Invalid choice, try again.[/error]")


def ask_multi_choice(
    question: str,
    choices: list[str],
    console: Console,
    default: list[str] | None = None,
) -> list[str]:
    console.print(f"[primary]{question}[/primary]")
    for idx, choice in enumerate(choices, start=1):
        console.print(f"  [accent]{idx}[/accent]) {choice}")

    default_str = ",".join(str(choices.index(d) + 1) for d in (default or []) if d in choices)

    if default_str:
        raw = Prompt.ask(
            "Choose (comma-separated)",
            console=console,
            default=default_str,
        )
    else:
        raw = Prompt.ask("Choose (comma-separated)", console=console)

    selected: list[str] = []
    for raw_piece in raw.split(","):
        piece = raw_piece.strip()
        if not piece:
            continue
        if piece.isdigit():
            index = int(piece)
            if 1 <= index <= len(choices):
                selected.append(choices[index - 1])
        elif piece in choices:
            selected.append(piece)
    return list(dict.fromkeys(selected))


def ask_table_row(console: Console, row: dict[str, Any]) -> None:
    for key, value in row.items():
        console.print(f"[muted]{key}:[/muted] {value}")
