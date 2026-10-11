from __future__ import annotations

from rich.console import Console

from zerosys.cli.ui.prompts import ask_confirm
from zerosys.wizard.hints import hint
from zerosys.wizard.steps.base import WizardState, WizardStep


class ServicesStep(WizardStep):
    name = "services"
    title = "Services"

    def run(self, state: WizardState, console: Console) -> None:
        self.render_hint(console, hint("nginx"))
        state.install_nginx = ask_confirm(
            "Install nginx (web server)?",
            console=console,
            default=state.install_nginx,
        )

        self.render_hint(console, hint("docker"))
        state.install_docker = ask_confirm(
            "Install Docker?",
            console=console,
            default=state.install_docker,
        )

        if state.install_nginx and 80 not in state.firewall_allow:
            state.firewall_allow = sorted({*state.firewall_allow, 80})
            state.add_note("Opened port 80 for nginx")
        if state.install_nginx and 443 not in state.firewall_allow:
            state.firewall_allow = sorted({*state.firewall_allow, 443})
            state.add_note("Opened port 443 for nginx")
