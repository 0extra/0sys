from __future__ import annotations

from rich.console import Console

from zerosys.cli.ui.prompts import ask_confirm, ask_multi_choice
from zerosys.wizard.hints import hint
from zerosys.wizard.steps.base import WizardState, WizardStep


class SecurityStep(WizardStep):
    name = "security"
    title = "Firewall and protection"

    def run(self, state: WizardState, console: Console) -> None:
        self.render_hint(console, hint("firewall_default"))
        strict = ask_confirm(
            "Close all ports by default and only open what we need?",
            console=console,
            default=state.firewall_default == "deny",
        )
        state.firewall_default = "deny" if strict else "allow"

        self.render_hint(console, hint("firewall"))
        common_ports = {
            "SSH (22) - you need this to log in": 22,
            "HTTP (80) - unencrypted web": 80,
            "HTTPS (443) - encrypted web": 443,
            "PostgreSQL (5432)": 5432,
            "MySQL / MariaDB (3306)": 3306,
            "Redis (6379)": 6379,
            "MongoDB (27017)": 27017,
        }
        labels = list(common_ports.keys())
        preselected = [
            label for label, port in common_ports.items() if port in state.firewall_allow
        ]
        chosen = ask_multi_choice(
            "Which ports should be open?",
            choices=labels,
            console=console,
            default=preselected,
        )
        state.firewall_allow = sorted({common_ports[label] for label in chosen} or {22})

        self.render_hint(console, hint("fail2ban"))
        state.install_fail2ban = ask_confirm(
            "Install fail2ban to block repeated login attempts?",
            console=console,
            default=state.install_fail2ban,
        )
