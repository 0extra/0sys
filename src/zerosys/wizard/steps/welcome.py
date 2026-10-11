from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from zerosys.wizard.steps.base import WizardState, WizardStep


class WelcomeStep(WizardStep):
    name = "welcome"
    title = "Welcome"

    def run(self, state: WizardState, console: Console) -> None:
        body = Text()
        body.append("I will help you write a small config file.\n", style="primary")
        body.append("\n")
        body.append("I ask questions one at a time and explain each one.\n")
        body.append("Nothing is sent to your server yet. ")
        body.append("You can stop with Ctrl+C at any moment.\n")
        body.append("\n")
        body.append("When we are done, you review the plan and decide ", style="muted")
        body.append("yes", style="accent")
        body.append(" or ", style="muted")
        body.append("no", style="accent")
        body.append(".", style="muted")
        console.print(Panel(body, border_style="info", padding=(1, 2), title="0sys wizard"))
