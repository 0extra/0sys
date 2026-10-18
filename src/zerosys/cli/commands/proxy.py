from __future__ import annotations

import secrets
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from platformdirs import user_data_dir
from rich.console import Console
from rich.table import Table
from rich.text import Text

from zerosys.cli.ui.theme import get_console
from zerosys.core.errors import StateError
from zerosys.core.state import StateStore

DEFAULT_STATE_DIR = "0sys"
DEFAULT_STATE_AUTHOR = "0extra"
DEFAULT_SERVER_CERT_DIR = "/opt/0tpe"
DEFAULT_FETCH_TIMEOUT = 60
CERT_FILES = ("ca.crt", "client.crt", "client.key", "server.crt")
PRIVATE_CERT_FILES = frozenset({"client.key", "ca.key", "server.key"})


def _default_state_path() -> Path:
    return Path(user_data_dir(DEFAULT_STATE_DIR, DEFAULT_STATE_AUTHOR)) / "state.db"


@dataclass(frozen=True)
class ProxyInfo:
    host: str
    run_id: str
    params: dict[str, Any]

    def port(self) -> int:
        return int(self.params.get("port", 8443))

    def sni(self) -> str:
        return str(self.params.get("sni", "www.microsoft.com"))

    def max_connections(self) -> int:
        return int(self.params.get("max_connections", 512))

    def log_level(self) -> str:
        return str(self.params.get("log_level", "info"))

    def version(self) -> str:
        return str(self.params.get("version", "0.1.8"))


def _latest_proxy_info(store: StateStore) -> ProxyInfo | None:
    runs = store.list_runs(limit=50)
    for record in runs:
        tasks = store.get_tasks(record.id)
        for task in tasks:
            if task.kind.value != "proxy":
                continue
            if task.status.value != "success":
                continue
            return ProxyInfo(
                host=record.target_host,
                run_id=record.id,
                params=dict(task.params),
            )
    return None


def _open_store(state_path: Path | None, console: Console) -> StateStore:
    store = StateStore(state_path or _default_state_path())
    try:
        store.connect()
    except StateError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc
    return store


def _resolve_proxy_host(
    host: str | None,
    state_path: Path | None,
    console: Console,
) -> str | None:
    if host is not None:
        return host
    store = _open_store(state_path, console)
    info = _latest_proxy_info(store)
    store.close()
    return info.host if info else None


def proxy_server_info_command(
    state_path: Path | None = typer.Option(
        None,
        "--state-path",
        help="Custom path to state database",
    ),
) -> None:
    console = get_console()
    store = _open_store(state_path, console)
    info = _latest_proxy_info(store)
    store.close()

    if info is None:
        console.print("[warning]No successful proxy run found.[/warning]")
        console.print("[hint]Apply a config with 'proxy.enabled: true' first.[/hint]")
        raise typer.Exit(code=1)

    table = Table(title="0TPE server", border_style="primary")
    table.add_column("Field", style="task.kind")
    table.add_column("Value")
    table.add_row("Host", info.host)
    table.add_row("Port", str(info.port()))
    table.add_row("SNI", info.sni())
    table.add_row("Max connections", str(info.max_connections()))
    table.add_row("Log level", info.log_level())
    table.add_row("Version", info.version())
    table.add_row("Run id", info.run_id)
    console.print(table)


def proxy_client_config_command(
    host: str | None = typer.Option(None, "--host", "-H", help="Server address"),
    port: int | None = typer.Option(None, "--port", "-p", help="Server port"),
    sni: str | None = typer.Option(None, "--sni", help="Fallback SNI hostname"),
    socks_port: int = typer.Option(1080, "--socks-port", help="Local SOCKS port"),
    http_port: int = typer.Option(8080, "--http-port", help="Local HTTP port"),
    max_udp_sessions: int = typer.Option(32, "--max-udp-sessions"),
    token: str | None = typer.Option(None, "--token", help="Auth token"),
    ca_file: str = typer.Option("certs/ca.crt", "--ca-file"),
    client_cert_file: str = typer.Option("certs/client.crt", "--client-cert"),
    client_key_file: str = typer.Option("certs/client.key", "--client-key"),
    log_level: str = typer.Option("info", "--log-level"),
    output: Path = typer.Option(
        Path("client.conf"),
        "--output",
        "-o",
        help="Where to write the client config",
    ),
    state_path: Path | None = typer.Option(
        None,
        "--state-path",
        help="Custom path to state database",
    ),
) -> None:
    console = get_console()

    if host is None or port is None or sni is None:
        store = _open_store(state_path, console)
        info = _latest_proxy_info(store)
        store.close()
        if info is not None:
            host = host or info.host
            port = port or info.port()
            sni = sni or info.sni()

    if host is None or port is None or sni is None:
        console.print(
            "[error]Need --host, --port and --sni, or a successful proxy run in state.[/error]"
        )
        raise typer.Exit(code=1)

    if token is None:
        token = secrets.token_hex(16)

    lines = [
        "# 0TPE client config generated by 0sys",
        "",
        f"server_ip        = {host}",
        f"server_port      = {port}",
        f"socks_port       = {socks_port}",
        f"http_port        = {http_port}",
        f"max_udp_sessions = {max_udp_sessions}",
        f"sni              = {sni}",
        f"token            = {token}",
        f"ca_file          = {ca_file}",
        f"client_cert_file = {client_cert_file}",
        f"client_key_file  = {client_key_file}",
        "",
        f"log_level = {log_level}",
        "",
    ]
    target = output.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")

    console.print(f"[success]Wrote {target}[/success]")
    console.print(
        "[hint]Copy this file along with certs/ (ca.crt, client.crt, client.key) "
        "to your client machine and run 'otpe-client client.conf'.[/hint]"
    )


def proxy_show_config_command(
    state_path: Path | None = typer.Option(
        None,
        "--state-path",
        help="Custom path to state database",
    ),
) -> None:
    console = get_console()
    store = _open_store(state_path, console)
    info = _latest_proxy_info(store)
    store.close()

    if info is None:
        console.print("[warning]No successful proxy run found.[/warning]")
        raise typer.Exit(code=1)

    lines = [
        "# 0TPE server config (reconstructed from state)",
        "",
        "listen_ip       = 0.0.0.0",
        f"listen_port     = {info.port()}",
        f"max_connections = {info.max_connections()}",
        "cert_file       = certs/server.crt",
        "key_file        = certs/server.key",
        "ca_file         = certs/ca.crt",
        f"fallback_sni    = {info.sni()}",
        "",
        f"log_level = {info.log_level()}",
        "",
    ]
    console.print(Text("\n".join(lines)))


def _build_scp_argv(
    host: str,
    user: str,
    port: int,
    ssh_key: str | None,
    remote_path: str,
    local_path: Path,
) -> list[str]:
    argv = ["scp"]
    argv.extend(["-o", "StrictHostKeyChecking=accept-new"])
    argv.extend(["-o", "BatchMode=yes"])
    if port != 22:
        argv.extend(["-P", str(port)])
    if ssh_key:
        argv.extend(["-i", ssh_key])
    argv.append(f"{user}@{host}:{remote_path}")
    argv.append(str(local_path))
    return argv


def _fetch_one_cert(
    name: str,
    remote_dir: str,
    host: str,
    user: str,
    port: int,
    ssh_key: str | None,
    target_dir: Path,
    console: Console,
) -> bool:
    remote_path = f"{remote_dir}/certs/{name}"
    local_path = target_dir / name
    argv = _build_scp_argv(host, user, port, ssh_key, remote_path, local_path)

    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=DEFAULT_FETCH_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        console.print(f"[warning]scp failed for {name}: {exc}[/warning]")
        return False

    if completed.returncode != 0:
        console.print(f"[warning]Cannot fetch {name}: {completed.stderr.strip()}[/warning]")
        return False

    local_path.chmod(0o600 if name in PRIVATE_CERT_FILES else 0o644)
    return True


def _print_fetched_certs(console: Console, target: Path, names: list[str]) -> None:
    console.print(f"[success]Fetched {len(names)} file(s) to {target}[/success]")
    for name in names:
        console.print(f"  [accent]{name}[/accent]")
    console.print("")
    console.print("[primary]Next:[/primary]")
    console.print("  otpe-client client.conf")


def proxy_fetch_certs_command(
    host: str | None = typer.Option(None, "--host", "-H", help="Server address"),
    user: str = typer.Option("root", "--user", "-u", help="SSH user"),
    port: int = typer.Option(22, "--port", "-p", help="SSH port"),
    ssh_key: str | None = typer.Option(None, "--ssh-key", help="Path to SSH private key"),
    remote_dir: str = typer.Option(
        DEFAULT_SERVER_CERT_DIR,
        "--remote-dir",
        help="Directory on the server that contains certs/",
    ),
    output_dir: Path = typer.Option(
        Path.home() / ".config" / "0tpe" / "certs",
        "--output",
        "-o",
        help="Local directory to store the certificates",
    ),
    state_path: Path | None = typer.Option(
        None,
        "--state-path",
        help="Custom path to state database",
    ),
) -> None:
    console = get_console()

    resolved_host = _resolve_proxy_host(host, state_path, console)
    if resolved_host is None:
        console.print("[error]Need --host or a successful proxy run in state.[/error]")
        raise typer.Exit(code=1)

    target = output_dir.expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)

    fetched = [
        name
        for name in CERT_FILES
        if _fetch_one_cert(
            name=name,
            remote_dir=remote_dir,
            host=resolved_host,
            user=user,
            port=port,
            ssh_key=ssh_key,
            target_dir=target,
            console=console,
        )
    ]

    if not fetched:
        console.print("[error]No certificates fetched.[/error]")
        raise typer.Exit(code=1)

    _print_fetched_certs(console, target, fetched)
