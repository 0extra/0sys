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

app = typer.Typer(help="Create a starter configuration file")

PRESETS = {
    "minimal": minimal_config,
    "web": web_server_config,
    "docker": docker_host_config,
}


@app.callback(invoke_without_command=True)
def run(
    preset: str = typer.Option("minimal", "--preset", help="Preset name: minimal, web, docker"),
    output: Path = typer.Option(Path(DEFAULT_CONFIG_FILENAME), "--output", "-o"),
    hostname: str | None = typer.Option(None, "--hostname"),
) -> None:
    console = get_console()

    if preset not in PRESETS:
        console.print(f"[error]Unknown preset '{preset}'. Choose: {', '.join(PRESETS)}[/error]")
        raise typer.Exit(code=1)

    cfg = PRESETS[preset](hostname=hostname)
    path = write_config(cfg, output)
    console.print(f"[success]Wrote {path}[/success]")
    console.print("[hint]Run: 0sys plan " + str(output) + "[/hint]")
