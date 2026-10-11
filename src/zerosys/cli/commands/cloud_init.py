from __future__ import annotations

from pathlib import Path

import typer
from rich.text import Text

from zerosys.backends.cloudinit import CloudInitBackend
from zerosys.cli.ui.theme import get_console
from zerosys.core.config import load_config
from zerosys.core.errors import ConfigError

DEFAULT_OUTPUT = Path("user-data.yaml")


def cloud_init_command(
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
        help="Where to write the cloud-init file",
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

    backend = CloudInitBackend()
    content = backend.generate(cfg)

    if print_stdout:
        console.print(Text(content))
        return

    target = backend.write(cfg, output)
    console.print(f"[success]Wrote {target}[/success]")
    console.print(
        "[hint]Paste this file into your VPS provider's user-data field "
        "or pass it with cloud-init.[/hint]"
    )
