from __future__ import annotations

from pathlib import Path

import typer
from rich.text import Text

from zerosys.backends.terraform import TerraformBackend, TerraformError
from zerosys.cli.ui.theme import get_console
from zerosys.core.config import load_config
from zerosys.core.errors import ConfigError

DEFAULT_OUTPUT_DIR = Path("terraform")


def terraform_command(
    config: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to config file",
    ),
    output_dir: Path = typer.Option(
        DEFAULT_OUTPUT_DIR,
        "--output",
        "-o",
        help="Directory for generated .tf files",
    ),
) -> None:
    console = get_console()

    try:
        cfg = load_config(config)
    except ConfigError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    backend = TerraformBackend()

    try:
        written = backend.write(cfg, output_dir)
    except TerraformError as exc:
        console.print(Text(str(exc), style="error"))
        console.print(
            "[hint]Add an 'infrastructure' section to your config to use this command.[/hint]"
        )
        raise typer.Exit(code=1) from exc

    console.print(f"[success]Wrote {len(written)} file(s) to {output_dir}[/success]")
    for path in written:
        console.print(f"  [accent]{path.name}[/accent]")

    console.print("")
    console.print("[primary]Next steps:[/primary]")
    console.print(f"  1. cd {output_dir}")
    console.print("  2. terraform init")
    console.print("  3. terraform plan")
    console.print("  4. terraform apply")
