from __future__ import annotations

from pathlib import Path

import typer

from zerosys.cli.commands.apply import _apply_impl


def check_command(
    config: Path = typer.Argument(..., exists=True, readable=True),
    host: str = typer.Option("localhost", "--host", "-H"),
    user: str | None = typer.Option(None, "--user", "-u"),
    port: int = typer.Option(22, "--port", "-p"),
    ssh_key: str | None = typer.Option(None, "--ssh-key"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    tags: str | None = typer.Option(None, "--tags"),
) -> None:
    _apply_impl(
        config=config,
        host=host,
        user=user,
        port=port,
        ssh_key=ssh_key,
        dry_run=True,
        verbose=verbose,
        quiet=False,
        tags=tags,
        backend=None,
        stop_on_failure=True,
        rollback=False,
        state_path=None,
        yes=True,
        force_no_state=True,
    )
