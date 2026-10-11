from __future__ import annotations

from pathlib import Path

import typer
from platformdirs import user_data_dir

from zerosys.cli.ui.explainer import print_error, print_success, print_warning
from zerosys.cli.ui.theme import get_console
from zerosys.core.errors import StateError
from zerosys.core.state import StateStore

app = typer.Typer(help="Show recorded runs and roll back a previous one")


def _default_state_path() -> Path:
    return Path(user_data_dir("0sys", "0extra")) / "state.db"


@app.callback(invoke_without_command=True)
def run(
    run_id: str | None = typer.Argument(None, help="Run id to inspect"),
    state_path: Path | None = typer.Option(
        None,
        "--state-path",
        help="Custom state database path",
    ),
    list_runs: bool = typer.Option(False, "--list", "-l", help="List recent runs"),
) -> None:
    console = get_console()
    store = StateStore(state_path or _default_state_path())
    try:
        store.connect()
    except StateError as exc:
        print_error(str(exc), console)
        raise typer.Exit(code=1) from exc

    if list_runs or run_id is None:
        runs = store.list_runs(limit=20)
        if not runs:
            print_warning("No runs recorded yet.", console)
            store.close()
            raise typer.Exit(code=0)
        for existing in runs:
            console.print(
                f"[accent]{existing.id}[/accent] "
                f"[muted]{existing.started_at}[/muted] "
                f"[primary]{existing.status.value}[/primary] "
                f"[muted]{existing.target_host}[/muted] "
                f"[muted]{existing.successful_tasks}/{existing.total_tasks}[/muted]"
            )
        store.close()
        raise typer.Exit(code=0)

    record = store.get_run(run_id)
    if record is None:
        print_error(f"Run '{run_id}' not found.", console)
        store.close()
        raise typer.Exit(code=1)

    console.print(f"[primary]Run:[/primary] {record.id}")
    console.print(f"[muted]Started:[/muted] {record.started_at}")
    console.print(f"[muted]Finished:[/muted] {record.finished_at}")
    console.print(f"[muted]Status:[/muted] {record.status.value}")
    console.print(f"[muted]Host:[/muted] {record.target_host}")

    tasks = store.get_tasks(run_id)
    console.print(f"[muted]Tasks:[/muted] {len(tasks)}")
    for task in tasks:
        console.print(
            f"  [accent]{task.kind.value}[/accent] [muted]{task.name}[/muted] "
            f"[primary]{task.status.value}[/primary]"
        )

    print_warning("Automatic rollback is not enabled in this build.", console)
    store.close()
    print_success("Done.", console)
