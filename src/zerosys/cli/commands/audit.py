from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from zerosys.cli.ui.theme import get_console
from zerosys.connection.local import LocalConnection
from zerosys.connection.ssh import SshConnection
from zerosys.core.audit import AuditScanner
from zerosys.core.audit.scanner import AuditResult, DiscoveryStatus
from zerosys.core.config.parser import write_config

DEFAULT_OUTPUT = Path("audited-config.yaml")

_STATUS_STYLES: dict[DiscoveryStatus, str] = {
    DiscoveryStatus.SUCCESS: "success",
    DiscoveryStatus.PARTIAL: "warning",
    DiscoveryStatus.FAILED: "error",
    DiscoveryStatus.UNSUPPORTED: "muted",
}


def _render_discovery_table(console: Console, result: AuditResult) -> None:
    table = Table(title="Discovery summary", border_style="primary")
    table.add_column("Source", style="task.kind")
    table.add_column("Status")
    table.add_column("Count", style="muted")
    table.add_column("Detail", style="muted")
    for name, discovered in (
        ("packages", result.packages),
        ("services", result.services),
        ("users", result.users),
        ("firewall", result.firewall_ports),
    ):
        style = _STATUS_STYLES[discovered.status]
        table.add_row(
            name,
            f"[{style}]{discovered.status.value}[/{style}]",
            str(discovered.count()),
            discovered.detail,
        )
    console.print(table)


def audit_command(
    output: Path = typer.Option(
        DEFAULT_OUTPUT,
        "--output",
        "-o",
        help="Where to write the generated config",
    ),
    host: str = typer.Option(
        "localhost",
        "--host",
        "-H",
        help="Target host",
    ),
    user: str | None = typer.Option(
        None,
        "--user",
        "-u",
        help="SSH user",
    ),
    port: int = typer.Option(
        22,
        "--port",
        "-p",
        help="SSH port",
    ),
    ssh_key: str | None = typer.Option(
        None,
        "--ssh-key",
        help="Path to SSH private key",
    ),
) -> None:
    console = get_console()

    conn: LocalConnection | SshConnection

    if host in ("localhost", "127.0.0.1", "::1"):
        console.print("[primary]Auditing localhost...[/primary]")
        conn = LocalConnection()
    else:
        console.print(f"[primary]Auditing {user}@{host}:{port}...[/primary]")
        conn = SshConnection(
            host=host,
            user=user,
            port=port,
            key_file=Path(ssh_key) if ssh_key else None,
        )

    try:
        scanner = AuditScanner(conn)
        config, result = scanner.scan()
    except Exception as exc:
        console.print(Text(f"Audit failed: {exc}", style="error"))
        raise typer.Exit(code=1) from exc
    finally:
        conn.close()

    path = write_config(config, output)

    console.print(f"[success]Wrote {path}[/success]")
    console.print("")
    _render_discovery_table(console, result)

    if result.warnings:
        console.print("")
        console.print("[warning]Warnings:[/warning]")
        for warning in result.warnings:
            console.print(f"  [warning]•[/warning] {warning}")

    console.print("")
    console.print(
        "[warning]This is a partial snapshot. Review carefully before '0sys apply'.[/warning]"
    )
    console.print("[hint]Users are created without sudo by default.[/hint]")
