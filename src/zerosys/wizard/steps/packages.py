from __future__ import annotations

from rich.console import Console

from zerosys.cli.ui.prompts import ask_text
from zerosys.wizard.hints import hint
from zerosys.wizard.steps.base import WizardState, WizardStep


class PackagesStep(WizardStep):
    name = "packages"
    title = "Extra packages"

    def run(self, state: WizardState, console: Console) -> None:
        self.render_hint(console, hint("extra_packages"))
        raw = ask_text(
            "Extra packages (comma-separated, or empty)",
            console=console,
            default="",
        )
        packages = [p.strip() for p in raw.split(",") if p.strip()]
        state.extra_packages = list(dict.fromkeys(packages))
        if state.extra_packages:
            state.add_note(f"Extra packages: {', '.join(state.extra_packages)}")
