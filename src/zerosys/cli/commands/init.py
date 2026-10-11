from __future__ import annotations

from pathlib import Path

import typer

from zerosys.cli.ui.theme import get_console
from zerosys.core.config import (
    DEFAULT_CONFIG_FILENAME,
    docker_host_config,
    minimal_config,
    web_server_config,
    write_config,
)
from zerosys.wizard import run_wizard

app = typer.Typer(help="Create a starter configuration file")

PRESETS = {
    "minimal": minimal_config,
    "web": web_server_config,
    "docker": docker_host_config,
}


@app.callback(invoke_without_command=True)
def run(
    preset: str | None = typer.Option(
        None,
        "--preset",
        help="Skip the wizard and use a preset: minimal, web, docker",
    ),
    output: Path = typer.Option(
        Path(DEFAULT_CONFIG_FILENAME),
        "--output",
        "-o",
        help="Where to write the config",
    ),
    hostname: str | None = typer.Option(
        None,
        "--hostname",
        help="Hostname (only used with --preset)",
    ),
) -> None:
    console = get_console()

    if preset is None:
        run_wizard(output=output)
        return

    if preset not in PRESETS:
        console.print(f"[error]Unknown preset '{preset}'. Choose: {', '.join(PRESETS)}[/error]")
        raise typer.Exit(code=1)

    cfg = PRESETS[preset](hostname=hostname)
    path = write_config(cfg, output)
    console.print(f"[success]Wrote {path}[/success]")
    console.print(f"[hint]Run: 0sys plan {path}[/hint]")
