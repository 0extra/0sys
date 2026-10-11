from __future__ import annotations

from pathlib import Path

import typer
from rich.text import Text

from zerosys.cli.ui.theme import get_console

app = typer.Typer(help="Show example configurations")

EXAMPLES: dict[str, str] = {
    "minimal": """version: 1
server:
  hostname: my-server
  timezone: UTC
firewall:
  default: deny
  allow: [22]
""",
    "web": """version: 1
server:
  hostname: web-01
  timezone: UTC
packages:
  install: [nginx, ufw]
services:
  nginx:
    state: started
    enabled: true
firewall:
  default: deny
  allow: [22, 80, 443]
""",
    "docker": """version: 1
server:
  hostname: docker-01
packages:
  install: [docker, docker-compose, ufw]
services:
  docker:
    state: started
    enabled: true
firewall:
  default: deny
  allow: [22]
""",
}


@app.callback(invoke_without_command=True)
def run(
    name: str | None = typer.Argument(None, help="Example name"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Write example to file"),
) -> None:
    console = get_console()

    if name is None:
        console.print("[primary]Available examples:[/primary]")
        for key in sorted(EXAMPLES):
            console.print(f"  [accent]{key}[/accent]")
        console.print("[hint]Run: 0sys examples <name>[/hint]")
        raise typer.Exit(code=0)

    if name not in EXAMPLES:
        console.print(f"[error]Unknown example '{name}'[/error]")
        raise typer.Exit(code=1)

    content = EXAMPLES[name]

    if output is not None:
        output.write_text(content, encoding="utf-8")
        console.print(f"[success]Wrote {output}[/success]")
        return

    console.print(Text(content))
