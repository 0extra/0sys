from __future__ import annotations

import sys

import typer

from zerosys.cli.commands import (
    apply_command,
    check_command,
    cloud_init_command,
    nixos_command,
    plan_command,
    proxy_client_config_command,
    proxy_fetch_certs_command,
    proxy_server_info_command,
    proxy_show_config_command,
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

proxy_app = typer.Typer(help="Manage the 0TPE proxy server")
proxy_app.command(
    "server-info",
    help="Show proxy server details from state",
)(proxy_server_info_command)
proxy_app.command(
    "client-config",
    help="Generate a client config file",
)(proxy_client_config_command)
proxy_app.command(
    "show-config",
    help="Show reconstructed server config",
)(proxy_show_config_command)
proxy_app.command(
    "fetch-certs",
    help="Download certificates from the server",
)(proxy_fetch_certs_command)


app.command("plan", help="Show what 0sys would do")(plan_command)
app.command("apply", help="Apply a configuration")(apply_command)
app.command("check", help="Dry-run a configuration")(check_command)
app.command(
    "rollback",
    help="Inspect past runs and roll back safe operations",
)(rollback_command)
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

app.add_typer(doctor_cmd.app, name="doctor", help="Check environment for missing pieces")
app.add_typer(examples_cmd.app, name="examples", help="Show example configurations")
app.add_typer(explain_cmd.app, name="explain", help="Explain a configuration in plain English")
app.add_typer(init_cmd.app, name="init", help="Create a starter configuration file")
app.add_typer(explain_term_cmd.app, name="explain-term", help="Explain a technical term")
app.add_typer(tips_cmd.app, name="tips", help="Show practical tips")
app.add_typer(proxy_app, name="0tpe", help="0TPE proxy server helpers")


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
