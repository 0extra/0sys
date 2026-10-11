from __future__ import annotations

import hashlib
from pathlib import Path

import typer
from platformdirs import user_data_dir
from rich.text import Text

from zerosys.backends.base import BackendContext
from zerosys.cli.ui.explainer import (
    print_error,
    print_success,
    print_task_error,
    print_task_finish,
    print_task_start,
)
from zerosys.cli.ui.progress import NullReporter, ProgressReporter
from zerosys.cli.ui.theme import get_console
from zerosys.core.config import load_config, validate
from zerosys.core.errors import ConfigError, ExecutorError, PlannerError, StateError
from zerosys.core.executor import ExecutionContext, ExecutionOptions, Executor
from zerosys.core.planner import build_plan
from zerosys.core.planner.task import Task, TaskStatus
from zerosys.core.state import StateStore
from zerosys.core.state.models import RunRecord, TaskRecord

app = typer.Typer(help="Apply a configuration to the target host")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _default_state_path() -> Path:
    return Path(user_data_dir("0sys", "0extra")) / "state.db"


def _apply_impl(
    config: Path,
    host: str,
    user: str | None,
    port: int,
    ssh_key: str | None,
    dry_run: bool,
    verbose: bool,
    quiet: bool,
    tags: str | None,
    backend: str | None,
    stop_on_failure: bool,
    rollback: bool,
    state_path: Path | None,
    yes: bool,
) -> None:
    console = get_console()

    try:
        raw_text = config.read_text(encoding="utf-8")
        cfg = load_config(config)
    except (OSError, ConfigError) as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    report = validate(cfg)
    for issue in report.issues:
        style = {"error": "error", "warning": "warning", "info": "info"}.get(
            issue.severity.value, "muted"
        )
        console.print(Text(str(issue), style=style))

    if report.has_errors:
        console.print("[error]Config has errors, apply aborted.[/error]")
        raise typer.Exit(code=2)

    try:
        plan = build_plan(cfg, forced_backend=backend)
    except PlannerError as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    if not yes and not dry_run:
        console.print(f"[warning]About to apply {plan.size()} task(s) to {host}[/warning]")
        answer = typer.prompt("Type 'yes' to continue", default="no")
        if answer.strip().lower() != "yes":
            console.print("[muted]Aborted by user.[/muted]")
            raise typer.Exit(code=0)

    options = ExecutionOptions(
        dry_run=dry_run,
        verbose=verbose,
        stop_on_failure=stop_on_failure,
        rollback_on_failure=rollback,
        tags=[t.strip() for t in tags.split(",") if t.strip()] if tags else [],
        state_path=state_path,
        config_path=config,
        config_hash=_hash_text(raw_text),
    )

    backend_context = BackendContext(
        target_host=host,
        target_user=user,
        target_port=port,
        ssh_key=ssh_key,
        dry_run=dry_run,
        verbose=verbose,
    )

    context = ExecutionContext(plan=plan, backend_context=backend_context, options=options)

    reporter: ProgressReporter | NullReporter
    if quiet:
        reporter = NullReporter()
    else:
        reporter = ProgressReporter(console=console, total=plan.size(), description="Applying")

    def on_start(task: Task) -> None:
        if not quiet:
            print_task_start(task, console)

    def on_finish(task: Task) -> None:
        if quiet:
            return
        print_task_finish(task, console)
        if task.status is TaskStatus.FAILED:
            print_task_error(task, console)
        reporter.advance(task)

    executor = Executor(context, on_task_start=on_start, on_task_finish=on_finish)

    store: StateStore | None = None
    run_record: RunRecord | None = None

    if not dry_run:
        try:
            store = StateStore(state_path or _default_state_path())
            run_record = RunRecord(
                config_path=str(config.resolve()),
                config_hash=options.config_hash,
                target_host=host,
                target_user=user,
                total_tasks=plan.size(),
                dry_run=dry_run,
            )
            store.save_run(run_record)
        except StateError as exc:
            console.print(Text(f"State store unavailable: {exc}", style="warning"))
            store = None
            run_record = None

    try:
        state = executor.execute()
    except ExecutorError as exc:
        print_error(str(exc), console)
        raise typer.Exit(code=1) from exc

    reporter.stop()

    if store is not None and run_record is not None:
        run_record.total_tasks = state.total
        run_record.successful_tasks = state.successful
        run_record.failed_tasks = state.failed
        run_record.skipped_tasks = state.skipped
        run_record.finish(state.final_status())
        try:
            store.update_run(run_record)
            task_records = [TaskRecord.from_task(run_record.id, t) for t in plan.tasks()]
            store.save_tasks(task_records)
        except StateError as exc:
            console.print(Text(f"Failed to persist state: {exc}", style="warning"))
        finally:
            store.close()

    if state.has_failures():
        print_error(f"Apply finished with failures: {state.summary()}", console)
        raise typer.Exit(code=1)

    print_success(f"Apply finished: {state.summary()}", console)


@app.callback(invoke_without_command=True)
def run(
    config: Path = typer.Argument(..., exists=True, readable=True, help="Path to config file"),
    host: str = typer.Option("localhost", "--host", "-H", help="Target host"),
    user: str | None = typer.Option(None, "--user", "-u", help="SSH user"),
    port: int = typer.Option(22, "--port", "-p", help="SSH port"),
    ssh_key: str | None = typer.Option(None, "--ssh-key", help="Path to SSH private key"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Do not change anything"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show backend output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags filter"),
    backend: str | None = typer.Option(None, "--backend", help="Force a specific backend"),
    stop_on_failure: bool = typer.Option(True, "--stop-on-failure/--keep-going"),
    rollback: bool = typer.Option(False, "--rollback", help="Rollback on failure"),
    state_path: Path | None = typer.Option(None, "--state-path", help="Custom state database path"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    _apply_impl(
        config=config,
        host=host,
        user=user,
        port=port,
        ssh_key=ssh_key,
        dry_run=dry_run,
        verbose=verbose,
        quiet=quiet,
        tags=tags,
        backend=backend,
        stop_on_failure=stop_on_failure,
        rollback=rollback,
        state_path=state_path,
        yes=yes,
    )
