from __future__ import annotations

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from zerosys.version import __version__

LOGO_LINES = [
    "  ___  ____  __   __",
    " / _ \\| ___| \\ \\ / /",
    "| | | |___ \\  \\ V / ",
    "| |_| |___) |  | |  ",
    " \\___/|____/   |_|  ",
]


def render_logo() -> Text:
    text = Text()
    for line in LOGO_LINES:
        text.append(line + "\n", style="banner")
    return text


def render_tagline() -> Text:
    return Text(
        "Friendly server automation for beginner sysadmins",
        style="hint",
    )


def print_banner(console: Console) -> None:
    body = Text()
    body.append_text(render_logo())
    body.append("\n")
    body.append_text(render_tagline())
    body.append(f"\n\nversion {__version__}", style="muted")
    panel = Panel(
        Align.center(body),
        border_style="primary",
        padding=(1, 4),
        title="0sys",
        subtitle="zero to sysadmin",
    )
    console.print(panel)


def print_mini_banner(console: Console) -> None:
    console.print(f"[banner]0sys[/banner] [muted]v{__version__}[/muted]")
