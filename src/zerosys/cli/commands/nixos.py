from __future__ import annotations

from pathlib import Path

import typer
from rich.text import Text

from zerosys.backends.nixos import NixosBackend
from zerosys.cli.ui.theme import get_console
from zerosys.core.config import load_config
from zerosys.core.errors import ConfigError

DEFAULT_OUTPUT = Path("configuration.nix")


def nixos_command(
    config: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to config file",
    ),
    output: Path = typer.Option(
        DEFAULT_OUTPUT,
        "--output",
        "-o",
        help="Where to write configuration.nix",
    ),
    print_stdout: bool = typer.Option(
        False,
        "--print",
        "-p",
        help="Print the generated file to stdout instead of writing it",
    ),
) -> None:
    console = get_console()

    try:
        cfg = load_config(config)
    except ConfigError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    backend = NixosBackend()
    content = backend.generate(cfg)

    if print_stdout:
        console.print(Text(content))
        return

    target = backend.write(cfg, output)
    console.print(f"[success]Wrote {target}[/success]")
    console.print(
        "[hint]Place this file next to hardware-configuration.nix "
        "and run 'nixos-rebuild switch'.[/hint]"
    )
