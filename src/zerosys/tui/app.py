from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any, ClassVar

from platformdirs import user_data_dir
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog

from zerosys.backends.base import BackendContext
from zerosys.core.config.parser import load_config
from zerosys.core.config.schema import Config
from zerosys.core.config.validator import validate
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.executor import Executor
from zerosys.core.executor.state import ExecutionState
from zerosys.core.planner.planner import build_plan
from zerosys.core.planner.task import Task, TaskStatus
from zerosys.core.state import StateStore
from zerosys.core.state.models import RunRecord, TaskRecord

BindingType = Binding | tuple[str, str] | tuple[str, str, str]


def _default_state_path() -> Path:
    return Path(user_data_dir("0sys", "0extra")) / "state.db"


class ConfirmScreen(ModalScreen[bool]):
    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #confirm-dialog {
        width: 64;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    #confirm-buttons {
        height: auto;
        align: right middle;
        margin-top: 1;
    }
    #confirm-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Label(self.message)
            with Horizontal(id="confirm-buttons"):
                yield Button("Cancel", id="confirm-cancel", variant="default")
                yield Button("Apply", id="confirm-accept", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-accept")


class ZeroSysTUI(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main-container {
        height: 1fr;
        layout: horizontal;
    }
    #sidebar {
        width: 35;
        height: 100%;
        border-right: solid $primary;
        padding: 1;
    }
    #content {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    .sidebar-button {
        width: 100%;
        margin-bottom: 1;
    }
    .section-title {
        margin-top: 1;
        margin-bottom: 1;
        text-style: bold;
        color: $accent;
    }
    .input-field {
        margin-bottom: 1;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config_path = Path("0sys.yaml")
        self.current_config: Config | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            with Vertical(id="sidebar"):
                yield Label("Config Path", classes="section-title")
                yield Input(
                    placeholder="0sys.yaml",
                    value=str(self.config_path),
                    id="config-path",
                    classes="input-field",
                )

                yield Label("Target Host", classes="section-title")
                yield Input(
                    placeholder="localhost",
                    value="localhost",
                    id="target-host",
                    classes="input-field",
                )

                yield Button(
                    "Load Config",
                    id="btn-load",
                    variant="primary",
                    classes="sidebar-button",
                )

                yield Label("Actions", classes="section-title")
                yield Button(
                    "Plan",
                    id="btn-plan",
                    classes="sidebar-button",
                    disabled=True,
                )
                yield Button(
                    "Check",
                    id="btn-check",
                    classes="sidebar-button",
                    disabled=True,
                )
                yield Button(
                    "Apply",
                    id="btn-apply",
                    variant="success",
                    classes="sidebar-button",
                    disabled=True,
                )

            with Vertical(id="content"):
                yield Label("Output Log", classes="section-title")
                yield RichLog(id="log", highlight=True, markup=True)
        yield Footer()

    def _get_log(self) -> RichLog:
        return self.query_one("#log", RichLog)

    def _target_host(self) -> str:
        return self.query_one("#target-host", Input).value.strip() or "localhost"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-load":
            self._handle_load()
        elif button_id == "btn-plan" and self.current_config:
            self._run_plan()
        elif button_id == "btn-check" and self.current_config:
            self._run_check(self._get_log())
        elif button_id == "btn-apply" and self.current_config:
            self._handle_apply_click()

    def _handle_load(self) -> None:
        log = self._get_log()
        path_input = self.query_one("#config-path", Input)
        self.config_path = Path(path_input.value)

        if not self.config_path.exists():
            log.write(f"[error]File not found: {self.config_path}[/error]")
            return

        try:
            self.current_config = load_config(self.config_path)
        except Exception as exc:
            log.write(f"[error]Failed to load config: {exc}[/error]")
            return

        log.write(f"[success]Loaded config: {self.config_path}[/success]")
        log.write(f"Version: {self.current_config.version}")
        self.query_one("#btn-plan", Button).disabled = False
        self.query_one("#btn-check", Button).disabled = False
        self.query_one("#btn-apply", Button).disabled = False

    def _handle_apply_click(self) -> None:
        target = self._target_host()
        message = (
            f"Apply {self.config_path} to {target}?\n\n"
            "This will modify the target system. Review the plan first."
        )
        log = self._get_log()
        self.push_screen(
            ConfirmScreen(message),
            lambda confirmed: self._on_apply_confirmed(confirmed, log),
        )

    def _on_apply_confirmed(self, confirmed: bool | None, log: RichLog) -> None:
        if confirmed:
            self._run_apply(log)
        else:
            log.write("[muted]Apply cancelled.[/muted]")

    def _run_plan(self) -> None:
        log = self._get_log()
        log.write("[primary]Building plan...[/primary]")

        config = self.current_config
        if config is None:
            return

        try:
            report = validate(config, connect_port=22)
            if report.has_errors:
                for issue in report.errors():
                    log.write(f"[error]{issue}[/error]")
                log.write("[error]Plan aborted due to validation errors.[/error]")
                return

            plan = build_plan(config)
            log.write(f"[success]Plan built: {plan.size()} tasks[/success]")
            for level_idx, level in enumerate(plan.levels(), 1):
                log.write(f"  Level {level_idx}:")
                for task in level:
                    log.write(f"    - {task.name} ({task.kind.value})")
        except Exception as exc:
            log.write(f"[error]Plan failed: {exc}[/error]")

    @work(thread=True)
    def _run_check(self, log: RichLog) -> None:
        self._execute(dry_run=True, log=log)

    @work(thread=True)
    def _run_apply(self, log: RichLog) -> None:
        self._execute(dry_run=False, log=log)

    def _execute(self, dry_run: bool, log: RichLog) -> None:
        mode = "[warning]CHECK (DRY-RUN)[/warning]" if dry_run else "[error]APPLY[/error]"
        self.call_from_thread(log.write, f"Starting {mode}...")

        config = self.current_config
        if config is None:
            self.call_from_thread(log.write, "[error]No config loaded.[/error]")
            return

        report = validate(config, connect_port=22)
        if report.has_errors:
            self.call_from_thread(log.write, "[error]Aborted due to validation errors.[/error]")
            return

        plan = build_plan(config)
        target_host = self._target_host()

        backend_ctx = BackendContext(target_host=target_host, dry_run=dry_run)
        options = ExecutionOptions(dry_run=dry_run)
        context = ExecutionContext(plan=plan, backend_context=backend_ctx, options=options)

        store: StateStore | None = None
        run_record: RunRecord | None = None
        if not dry_run:
            store, run_record, error = self._setup_state(plan, target_host)
            if store is None:
                self.call_from_thread(
                    log.write,
                    f"[error]State store unavailable: {error}. Apply aborted.[/error]",
                )
                return

        state = self._run_executor(context, store, run_record, log)
        if state is None:
            if store is not None:
                store.close()
            return

        if state.has_failures():
            self.call_from_thread(
                log.write, f"[error]Finished with failures: {state.summary()}[/error]"
            )
        else:
            self.call_from_thread(log.write, f"[success]Finished: {state.summary()}[/success]")

        if store is not None and run_record is not None:
            self._finalize_state(store, run_record, state, log)

    def _setup_state(
        self, plan: Any, target_host: str
    ) -> tuple[StateStore | None, RunRecord | None, str]:
        store = StateStore(_default_state_path())
        try:
            store.connect()
            run_record = RunRecord(
                config_path=str(self.config_path.resolve()),
                target_host=target_host,
                total_tasks=plan.size(),
                dry_run=False,
            )
            store.save_run(run_record)
            return store, run_record, ""
        except Exception as exc:
            store.close()
            return None, None, str(exc)

    def _run_executor(
        self,
        context: ExecutionContext,
        store: StateStore | None,
        run_record: RunRecord | None,
        log: RichLog,
    ) -> ExecutionState | None:
        saved_ids: set[str] = set()

        def on_start(task: Task) -> None:
            self.call_from_thread(log.write, f"[primary]→[/primary] {task.name} ...")

        def on_finish(task: Task) -> None:
            if task.status is TaskStatus.SUCCESS:
                changed = task.result.changed if task.result else False
                suffix = "(changed)" if changed else "(no change)"
                self.call_from_thread(log.write, f"[success]✓[/success] {task.name} {suffix}")
            elif task.status is TaskStatus.FAILED:
                self.call_from_thread(log.write, f"[error]✗[/error] {task.name}")

            if store and run_record and task.id not in saved_ids:
                with contextlib.suppress(Exception):
                    store.save_task(TaskRecord.from_task(run_record.id, task))
                    saved_ids.add(task.id)

        executor = Executor(context, on_task_start=on_start, on_task_finish=on_finish)
        try:
            return executor.execute()
        except Exception as exc:
            self.call_from_thread(log.write, f"[error]Execution error: {exc}[/error]")
            return None

    def _finalize_state(
        self,
        store: StateStore,
        run_record: RunRecord,
        state: ExecutionState,
        log: RichLog,
    ) -> None:
        run_record.successful_tasks = state.successful
        run_record.failed_tasks = state.failed
        run_record.skipped_tasks = state.skipped
        run_record.finish(state.final_status())
        try:
            store.update_run(run_record)
        except Exception as exc:
            self.call_from_thread(log.write, f"[warning]Failed to save run: {exc}[/warning]")
        finally:
            store.close()


def run_tui() -> None:
    app = ZeroSysTUI()
    app.run()
