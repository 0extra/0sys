from __future__ import annotations

import sys

import typer

from zerosys.cli.commands import (
    apply as apply_cmd,
)
from zerosys.cli.commands import (
    check as check_cmd,
)
from zerosys.cli.commands import (
    cloud_init_command,
    nixos_command,
    rollback_command,
    terraform_command,
)
from zerosys.cli.commands import (
    doctor as doctor_cmd,
)
from zerosys.cli.commands import (
    examples as examples_cmd,
)
from zerosys.cli.commands import (
    explain as explain_cmd,
)
from zerosys.cli.commands import (
    explain_term as explain_term_cmd,
)
from zerosys.cli.commands import (
    init as init_cmd,
)
from zerosys.cli.commands import (
    plan as plan_cmd,
)
from zerosys.cli.commands import (
    tips as tips_cmd,
)
from zerosys.cli.ui.banner import print_banner, print_mini_banner
from zerosys.cli.ui.theme import build_console

app = typer.Typer(
    name="0sys",
    help="Friendly server automation for beginner sysadmins",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)


app.add_typer(plan_cmd.app, name="plan", help="Show what 0sys would do")
app.add_typer(apply_cmd.app, name="apply", help="Apply a configuration")
app.add_typer(check_cmd.app, name="check", help="Dry-run a configuration")
app.add_typer(doctor_cmd.app, name="doctor", help="Check environment for missing pieces")
app.add_typer(examples_cmd.app, name="examples", help="Show example configurations")
app.add_typer(explain_cmd.app, name="explain", help="Explain a configuration in plain English")
app.add_typer(init_cmd.app, name="init", help="Create a starter configuration file")
app.add_typer(explain_term_cmd.app, name="explain-term", help="Explain a technical term")
app.add_typer(tips_cmd.app, name="tips", help="Show practical tips")
app.command(
    "cloud-init",
    help="Generate cloud-init user-data for a VPS provider",
)(cloud_init_command)
app.command(
    "terraform",
    help="Generate Terraform HCL to create infrastructure",
)(terraform_command)
app.command(
    "nixos",
    help="Generate a NixOS configuration.nix from the config",
)(nixos_command)
app.command(
    "rollback",
    help="Inspect past runs and roll back safe operations",
)(rollback_command)


def _version_callback(value: bool) -> None:
    if value:
        print_mini_banner(build_console())
        raise typer.Exit(code=0)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    no_banner: bool = typer.Option(False, "--no-banner", help="Do not show the banner"),
) -> None:
    if ctx.invoked_subcommand is None:
        console = build_console()
        if not no_banner:
            print_banner(console)
        console.print(ctx.get_help())
        raise typer.Exit(code=0)


def cli_main() -> None:
    try:
        app()
    except KeyboardInterrupt:
        console = build_console()
        console.print("\n[warning]Interrupted by user.[/warning]")
        sys.exit(130)


if __name__ == "__main__":
    cli_main()
