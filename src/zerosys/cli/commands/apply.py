from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import typer
from platformdirs import user_data_dir
from rich.console import Console
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


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _default_state_path() -> Path:
    return Path(user_data_dir("0sys", "0extra")) / "state.db"


LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _persist_task(
    store: StateStore | None,
    run_record: RunRecord | None,
    task: Task,
    saved_ids: set[str],
    console: Console,
    include_unfinished: bool = False,
) -> None:
    if store is None or run_record is None or task.id in saved_ids:
        return
    if not include_unfinished and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
        return
    try:
        store.save_task(TaskRecord.from_task(run_record.id, task))
    except StateError as exc:
        console.print(Text(f"Failed to persist task state: {exc}", style="warning"))
        return
    saved_ids.add(task.id)


def _finalize_run(
    store: StateStore | None,
    run_record: RunRecord | None,
    plan: Any,
    saved_ids: set[str],
    console: Console,
    status: TaskStatus,
) -> None:
    if store is None or run_record is None:
        return
    tasks = list(plan.tasks())
    run_record.total_tasks = len(tasks)
    run_record.successful_tasks = sum(1 for t in tasks if t.status is TaskStatus.SUCCESS)
    run_record.failed_tasks = sum(1 for t in tasks if t.status is TaskStatus.FAILED)
    run_record.skipped_tasks = sum(1 for t in tasks if t.status is TaskStatus.SKIPPED)
    run_record.finish(status)
    try:
        store.update_run(run_record)
        for task in tasks:
            _persist_task(store, run_record, task, saved_ids, console, include_unfinished=True)
    except StateError as exc:
        console.print(Text(f"Failed to persist state: {exc}", style="warning"))
    finally:
        store.close()


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
    force_no_state: bool,
) -> None:
    console = get_console()

    try:
        raw_text = config.read_text(encoding="utf-8")
        cfg = load_config(config)
    except (OSError, ConfigError) as exc:
        console.print(Text(str(exc), style="error"))
        raise typer.Exit(code=1) from exc

    report = validate(cfg, connect_port=port)
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

    if host in LOCAL_HOSTS and not dry_run:
        console.print(
            "[warning]Target is this computer (localhost): "
            "the configuration will change THIS machine.[/warning]"
        )

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
            if not force_no_state:
                console.print(Text(f"State store unavailable: {exc}", style="error"))
                console.print(
                    "[error]Aborted. Use --force-no-state to apply without saving history "
                    "(rollback will be unavailable).[/error]"
                )
                raise typer.Exit(code=1) from exc

            console.print(
                Text(
                    f"State store unavailable: {exc} (forcing apply without state)",
                    style="warning",
                )
            )
            store = None
            run_record = None

    reporter: ProgressReporter | NullReporter
    if quiet:
        reporter = NullReporter()
    else:
        reporter = ProgressReporter(console=console, total=plan.size(), description="Applying")

    saved_ids: set[str] = set()

    def on_start(task: Task) -> None:
        if not quiet:
            print_task_start(task, console)

    def on_finish(task: Task) -> None:
        _persist_task(store, run_record, task, saved_ids, console)
        if quiet:
            return
        print_task_finish(task, console)
        if task.status is TaskStatus.FAILED:
            print_task_error(task, console)
        reporter.advance(task)

    executor = Executor(context, on_task_start=on_start, on_task_finish=on_finish)

    try:
        state = executor.execute()
    except (ExecutorError, KeyboardInterrupt) as exc:
        reporter.stop()
        _finalize_run(store, run_record, plan, saved_ids, console, TaskStatus.FAILED)

        if isinstance(exc, KeyboardInterrupt):
            print_error(
                "Interrupted. Finished tasks were saved; see '0sys rollback --list'.",
                console,
            )
            raise typer.Exit(code=130) from exc

        print_error(str(exc), console)
        raise typer.Exit(code=1) from exc

    reporter.stop()
    _finalize_run(store, run_record, plan, saved_ids, console, state.final_status())

    if state.has_failures():
        print_error(f"Apply finished with failures: {state.summary()}", console)
        raise typer.Exit(code=1)

    print_success(f"Apply finished: {state.summary()}", console)


def apply_command(
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
    force_no_state: bool = typer.Option(
        False,
        "--force-no-state",
        help="Allow apply without saving state (rollback unavailable)",
    ),
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
        force_no_state=force_no_state,
    )
