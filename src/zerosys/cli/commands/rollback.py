from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer
from platformdirs import user_data_dir
from rich.console import Console
from rich.table import Table

from zerosys.backends.base import BackendContext
from zerosys.backends.registry import get_backend, load_default_backends
from zerosys.cli.ui.explainer import print_error, print_success, print_warning
from zerosys.cli.ui.theme import get_console
from zerosys.core.errors import StateError
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.rollback import Rollbacker, RollbackOptions, RollbackReport
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.task import Task, TaskKind, TaskResult, TaskStatus
from zerosys.core.state import StateStore
from zerosys.core.state.models import TaskRecord


def _default_state_path() -> Path:
    return Path(user_data_dir("0sys", "0extra")) / "state.db"


@dataclass
class _ReconstructedPlan:
    tasks: list[Task]

    def size(self) -> int:
        return len(self.tasks)


def _task_from_record(record: TaskRecord) -> Task:
    task = Task(
        id=record.task_id,
        kind=record.kind,
        name=record.name,
        target=record.target,
        backend=record.backend,
        params=dict(record.params),
    )
    task.status = record.status
    task.result = TaskResult(status=record.status, changed=record.changed)
    return task


def _print_dry_run(
    console: Console,
    tasks: list[Task],
    options: RollbackOptions,
) -> int:
    table = Table(title="Rollback preview", border_style="primary")
    table.add_column("Task", style="accent")
    table.add_column("Kind", style="task.kind")
    table.add_column("Status")
    table.add_column("Reason", style="muted")

    for task in reversed(tasks):
        if task.status is TaskStatus.ROLLED_BACK:
            table.add_row(task.name, task.kind.value, "[muted]skip[/muted]", "already rolled back")
            continue

        is_unchanged = task.result is not None and not task.result.changed
        is_held = not options.aggressive or task.kind not in (
            TaskKind.PACKAGES_INSTALL,
            TaskKind.USER,
        )

        if is_unchanged and is_held:
            table.add_row(
                task.name,
                task.kind.value,
                "[muted]skip[/muted]",
                "unchanged by this run",
            )
            continue

        if task.backend is None:
            table.add_row(task.name, task.kind.value, "[muted]skip[/muted]", "no backend")
            continue
        try:
            backend = get_backend(task.backend)
        except Exception:
            table.add_row(task.name, task.kind.value, "[muted]skip[/muted]", "backend missing")
            continue

        if not backend.can_rollback(task):
            table.add_row(task.name, task.kind.value, "[muted]skip[/muted]", "not reversible")
            continue

        if task.kind in (TaskKind.PACKAGES_INSTALL, TaskKind.USER) and not options.aggressive:
            table.add_row(
                task.name,
                task.kind.value,
                "[warning]hold[/warning]",
                "use --aggressive to remove packages and users",
            )
            continue

        table.add_row(task.name, task.kind.value, "[success]rollback[/success]", "")

    console.print(table)
    return 0


def _print_report(console: Console, report: RollbackReport) -> None:
    print_success(report.summary(), console)

    if report.not_reversible:
        console.print("[muted]Not reversible:[/muted]")
        for name in report.not_reversible:
            console.print(f"  [muted]•[/muted] {name}")


def _execute_rollback(
    run_id: str,
    store: StateStore,
    host: str | None,
    user: str | None,
    port: int | None,
    ssh_key: str | None,
    dry_run: bool,
    aggressive: bool,
) -> int:
    console = get_console()

    record = store.get_run(run_id)
    if record is None:
        print_error(f"Run '{run_id}' not found.", console)
        return 1

    task_records = store.get_tasks(run_id)
    if not task_records:
        print_warning("This run has no recorded tasks.", console)
        return 0

    executed = [_task_from_record(r) for r in task_records if r.status is TaskStatus.SUCCESS]
    if not executed:
        print_warning("No successful tasks to roll back.", console)
        return 0

    rollback_options = RollbackOptions(aggressive=aggressive, stop_on_failure=True)

    if dry_run:
        return _print_dry_run(console, executed, rollback_options)

    target_host = host if host is not None else record.target_host
    target_user = user if user is not None else record.target_user

    backend_context = BackendContext(
        target_host=target_host,
        target_user=target_user,
        target_port=port if port is not None else 22,
        ssh_key=ssh_key,
        dry_run=False,
    )
    options = ExecutionOptions(dry_run=False)
    context = ExecutionContext(
        plan=_ReconstructedPlan(executed),  # type: ignore[arg-type]
        backend_context=backend_context,
        options=options,
    )
    state = ExecutionState(total=len(executed))
    for task in executed:
        state.register_success(task)

    rollbacker = Rollbacker(context, state, rollback_options)
    report = rollbacker.rollback()

    _print_report(console, report)

    for task in executed:
        if task.status is TaskStatus.ROLLED_BACK:
            try:
                store.save_task(TaskRecord.from_task(run_id, task))
            except StateError:
                pass

    return 0 if report.failed == 0 else 1


def _list_runs(console: Console, store: StateStore) -> None:
    runs = store.list_runs(limit=20)
    if not runs:
        print_warning("No runs recorded yet.", console)
        return
    table = Table(title="Recent runs", border_style="primary")
    table.add_column("Run id", style="accent")
    table.add_column("Started", style="muted")
    table.add_column("Status")
    table.add_column("Host", style="muted")
    table.add_column("Tasks", style="muted")
    for record in runs:
        table.add_row(
            record.id,
            record.started_at,
            record.status.value,
            record.target_host,
            f"{record.successful_tasks}/{record.total_tasks}",
        )
    console.print(table)


def rollback_command(
    run_id: str | None = typer.Argument(None, help="Run id to roll back"),
    list_runs: bool = typer.Option(False, "--list", "-l", help="List recent runs"),
    state_path: Path | None = typer.Option(
        None,
        "--state-path",
        help="Custom path to state database",
    ),
    host: str | None = typer.Option(
        None,
        "--host",
        "-H",
        help="Target host (defaults to original run host)",
    ),
    user: str | None = typer.Option(None, "--user", "-u", help="SSH user"),
    port: int | None = typer.Option(None, "--port", "-p", help="SSH port"),
    ssh_key: str | None = typer.Option(None, "--ssh-key", help="Path to SSH private key"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be rolled back without executing",
    ),
    aggressive: bool = typer.Option(
        False,
        "--aggressive",
        help="Also remove packages and users created by the run (deletes data)",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    console = get_console()
    load_default_backends()
    store = StateStore(state_path or _default_state_path())
    try:
        store.connect()
    except StateError as exc:
        print_error(str(exc), console)
        raise typer.Exit(code=1) from exc

    if list_runs or run_id is None:
        _list_runs(console, store)
        store.close()
        raise typer.Exit(code=0)

    if not dry_run and not yes:
        record = store.get_run(run_id)
        target_host = host if host is not None else (record.target_host if record else "unknown")
        console.print(f"[warning]About to roll back run {run_id} on {target_host}.[/warning]")
        answer = typer.prompt("Type 'yes' to continue", default="no")
        if answer.strip().lower() != "yes":
            console.print("[muted]Aborted by user.[/muted]")
            store.close()
            raise typer.Exit(code=0)

    code = _execute_rollback(
        run_id=run_id,
        store=store,
        host=host,
        user=user,
        port=port,
        ssh_key=ssh_key,
        dry_run=dry_run,
        aggressive=aggressive,
    )
    store.close()
    raise typer.Exit(code=code)
