from __future__ import annotations

from rich.console import Console
from rich.table import Table

from zerosys.cli.ui.prompts import ask_confirm
from zerosys.wizard.hints import hint
from zerosys.wizard.steps.base import WizardState, WizardStep


class ReviewStep(WizardStep):
    name = "review"
    title = "Review"

    def run(self, state: WizardState, console: Console) -> None:
        table = Table(title="Summary", border_style="primary", show_header=False)
        table.add_column("Setting", style="task.kind")
        table.add_column("Value", style="white")

        for key, value in state.as_summary().items():
            table.add_row(key, str(value))

        console.print(table)

        if state.notes:
            console.print("[muted]Notes:[/muted]")
            for note in state.notes:
                console.print(f"  [muted]•[/muted] {note}")

        self.render_hint(console, hint("review"))
        confirmed = ask_confirm(
            "Does this look right?",
            console=console,
            default=True,
        )
        if not confirmed:
            raise SystemExit(0)
