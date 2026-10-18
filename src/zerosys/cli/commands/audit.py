from __future__ import annotations

from pathlib import Path

import typer
from rich.text import Text

from zerosys.cli.ui.theme import get_console
from zerosys.connection.local import LocalConnection
from zerosys.connection.ssh import SshConnection
from zerosys.core.audit import AuditScanner
from zerosys.core.config.parser import write_config

DEFAULT_OUTPUT = Path("audited-config.yaml")


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
        config = scanner.scan()
    except Exception as exc:
        console.print(Text(f"Audit failed: {exc}", style="error"))
        raise typer.Exit(code=1) from exc
    finally:
        conn.close()

    path = write_config(config, output)

    console.print(f"[success]Wrote {path}[/success]")
    console.print(f"  Packages found: {len(config.packages.install) if config.packages else 0}")
    console.print(f"  Services found: {len(config.services)}")
    console.print(f"  Users found:    {len(config.users)}")
    console.print("")

    warning_msg = (
        "WARNING: This is a partial snapshot. Packages are limited to 50, "
        "services to 20. Firewall rules are inferred from UFW and may be incomplete. "
        "Users are created without sudo by default."
    )
    console.print(f"[warning]{warning_msg}[/warning]")
    console.print("[hint]Review the file carefully before running '0sys apply'.[/hint]")
