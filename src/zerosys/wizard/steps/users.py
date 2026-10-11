from __future__ import annotations

from rich.console import Console

from zerosys.wizard.steps.base import WizardState, WizardStep


class UsersStep(WizardStep):
    name = "users"
    title = "Extra users"

    def should_skip(self, state: WizardState) -> bool:
        return True

    def run(self, state: WizardState, console: Console) -> None:
        console.print("[muted]Extra users can be added later by editing the config.[/muted]")
