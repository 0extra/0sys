from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console
from rich.theme import Theme


@dataclass(frozen=True)
class Palette:
    primary: str = "cyan"
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"
    info: str = "blue"
    muted: str = "bright_black"
    accent: str = "magenta"


PALETTE = Palette()

RICH_THEME = Theme(
    {
        "primary": PALETTE.primary,
        "success": PALETTE.success,
        "warning": PALETTE.warning,
        "error": PALETTE.error,
        "info": PALETTE.info,
        "muted": PALETTE.muted,
        "accent": PALETTE.accent,
        "banner": f"bold {PALETTE.primary}",
        "task.kind": f"bold {PALETTE.accent}",
        "task.name": "white",
        "task.target": PALETTE.muted,
        "task.success": f"bold {PALETTE.success}",
        "task.failure": f"bold {PALETTE.error}",
        "task.skip": PALETTE.muted,
        "task.rollback": PALETTE.warning,
        "hint": f"italic {PALETTE.muted}",
    }
)


def build_console(quiet: bool = False, no_color: bool = False) -> Console:
    return Console(
        theme=RICH_THEME,
        quiet=quiet,
        no_color=no_color,
        highlight=False,
        soft_wrap=False,
    )


class _ConsoleHolder:
    def __init__(self) -> None:
        self._console: Console | None = None

    def get(self) -> Console:
        if self._console is None:
            self._console = build_console()
        return self._console

    def set(self, console: Console) -> None:
        self._console = console

    def reset(self) -> None:
        self._console = None


_holder = _ConsoleHolder()


def get_console() -> Console:
    return _holder.get()


def set_console(console: Console) -> None:
    _holder.set(console)


def reset_console() -> None:
    _holder.reset()
