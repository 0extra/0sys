from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, RichLog

from zerosys.backends.base import BackendContext
from zerosys.core.config.parser import load_config
from zerosys.core.config.schema import Config
from zerosys.core.config.validator import validate
from zerosys.core.executor.context import ExecutionContext, ExecutionOptions
from zerosys.core.executor.executor import Executor
from zerosys.core.planner.planner import build_plan
from zerosys.core.planner.task import Task, TaskStatus

BindingType = Binding | tuple[str, str] | tuple[str, str, str]


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
        width: 30;
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
    #config-path {
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
                yield Label("Configuration", classes="section-title")
                yield Input(
                    placeholder="Path to config",
                    value=str(self.config_path),
                    id="config-path",
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#log", RichLog)

        if event.button.id == "btn-load":
            path_input = self.query_one("#config-path", Input)
            self.config_path = Path(path_input.value)

            if not self.config_path.exists():
                log.write(f"[error]File not found: {self.config_path}[/error]")
                return

            try:
                self.current_config = load_config(self.config_path)
                log.write(f"[success]Loaded config: {self.config_path}[/success]")
                log.write(f"Version: {self.current_config.version}")

                self.query_one("#btn-plan", Button).disabled = False
                self.query_one("#btn-check", Button).disabled = False
                self.query_one("#btn-apply", Button).disabled = False
            except Exception as exc:
                log.write(f"[error]Failed to load config: {exc}[/error]")

        elif event.button.id == "btn-plan" and self.current_config:
            self._run_plan()

        elif event.button.id == "btn-check" and self.current_config:
            self._run_check()

        elif event.button.id == "btn-apply" and self.current_config:
            self._run_apply()

    def _run_plan(self) -> None:
        log = self.query_one("#log", RichLog)
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
    def _run_check(self) -> None:
        self.call_from_thread(self._execute, dry_run=True)

    @work(thread=True)
    def _run_apply(self) -> None:
        self.call_from_thread(self._execute, dry_run=False)

    def _execute(self, dry_run: bool) -> None:
        log = self.query_one("#log", RichLog)
        mode = "[warning]CHECK (DRY-RUN)[/warning]" if dry_run else "[error]APPLY[/error]"
        log.write(f"Starting {mode}...")

        config = self.current_config
        if config is None:
            log.write("[error]No config loaded.[/error]")
            return

        report = validate(config, connect_port=22)
        if report.has_errors:
            log.write("[error]Aborted due to validation errors.[/error]")
            return

        plan = build_plan(config)
        backend_ctx = BackendContext(target_host="localhost", dry_run=dry_run)
        options = ExecutionOptions(dry_run=dry_run)
        context = ExecutionContext(plan=plan, backend_context=backend_ctx, options=options)

        def on_start(task: Task) -> None:
            log.write(f"[primary]→[/primary] {task.name} ...")

        def on_finish(task: Task) -> None:
            if task.status is TaskStatus.SUCCESS:
                changed = task.result.changed if task.result else False
                suffix = "(changed)" if changed else "(no change)"
                log.write(f"[success]✓[/success] {task.name} {suffix}")
            elif task.status is TaskStatus.FAILED:
                log.write(f"[error]✗[/error] {task.name}")

        executor = Executor(context, on_task_start=on_start, on_task_finish=on_finish)

        try:
            state = executor.execute()
            if state.has_failures():
                log.write(f"[error]Finished with failures: {state.summary()}[/error]")
            else:
                log.write(f"[success]Finished: {state.summary()}[/success]")
        except Exception as exc:
            log.write(f"[error]Execution error: {exc}[/error]")


def run_tui() -> None:
    app = ZeroSysTUI()
    app.run()
