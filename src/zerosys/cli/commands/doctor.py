from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass

import typer
from rich.console import Console
from rich.table import Table

from zerosys.cli.ui.theme import get_console
from zerosys.version import __version__

app = typer.Typer(help="Check the environment for missing dependencies")


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    required: bool = True


def _check_python() -> CheckResult:
    version = sys.version_info
    ok = version >= (3, 11)
    detail = f"{version.major}.{version.minor}.{version.micro}"
    return CheckResult("python", ok, detail)


def _check_module(module: str, required: bool = True) -> CheckResult:
    spec = importlib.util.find_spec(module)
    ok = spec is not None
    detail = "installed" if ok else "missing"
    return CheckResult(module, ok, detail, required=required)


def _check_binary(name: str, required: bool = False) -> CheckResult:
    path = shutil.which(name)
    ok = path is not None
    detail = path or "not found in PATH"
    return CheckResult(name, ok, detail, required=required)


def _check_ansible_collection(name: str) -> CheckResult:
    if shutil.which("ansible-galaxy") is None:
        return CheckResult(name, False, "ansible-galaxy not found", required=False)
    try:
        completed = subprocess.run(
            ["ansible-galaxy", "collection", "list", name],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CheckResult(name, False, str(exc), required=False)
    ok = completed.returncode == 0 and name in completed.stdout
    detail = "installed" if ok else "missing"
    return CheckResult(name, ok, detail, required=False)


def _render(console: Console, results: list[CheckResult]) -> None:
    table = Table(title="0sys doctor", border_style="primary")
    table.add_column("Check", style="task.kind")
    table.add_column("Status")
    table.add_column("Detail", style="muted")
    table.add_column("Required")

    for result in results:
        status = "[success]ok[/success]" if result.ok else "[error]fail[/error]"
        if not result.ok and not result.required:
            status = "[warning]warn[/warning]"
        table.add_row(
            result.name,
            status,
            result.detail,
            "[accent]yes[/accent]" if result.required else "[muted]no[/muted]",
        )
    console.print(table)


@app.callback(invoke_without_command=True)
def run() -> None:
    console = get_console()
    console.print(f"[primary]0sys doctor[/primary] [muted]v{__version__}[/muted]")

    results: list[CheckResult] = [
        _check_python(),
        _check_module("typer"),
        _check_module("rich"),
        _check_module("pydantic"),
        _check_module("yaml"),
        _check_module("jinja2"),
        _check_module("ansible_runner", required=False),
        _check_binary("ansible-playbook", required=False),
        _check_ansible_collection("community.general"),
        _check_ansible_collection("community.docker"),
        _check_ansible_collection("ansible.posix"),
        _check_binary("terraform", required=False),
        _check_binary("nixos-rebuild", required=False),
        _check_binary("docker", required=False),
        _check_binary("ssh", required=False),
        _check_binary("ssh-keygen", required=False),
    ]

    _render(console, results)

    missing_required = [r for r in results if r.required and not r.ok]
    missing_optional = [r for r in results if not r.required and not r.ok]

    if missing_required:
        console.print(
            f"[error]Missing required components: "
            f"{', '.join(r.name for r in missing_required)}[/error]"
        )
        raise typer.Exit(code=1)

    if missing_optional:
        names = ", ".join(r.name for r in missing_optional)
        console.print(f"[warning]Optional components missing: {names}[/warning]")
        console.print("[hint]Install them if you plan to use the related backends.[/hint]")

    console.print("[success]Environment looks good.[/success]")
