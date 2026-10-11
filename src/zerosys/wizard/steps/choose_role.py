from __future__ import annotations

from rich.console import Console

from zerosys.cli.ui.prompts import ask_choice
from zerosys.wizard.hints import hint
from zerosys.wizard.steps.base import WizardState, WizardStep

ROLE_LABELS: dict[str, str] = {
    "minimal": "Just secure a fresh server (SSH, firewall, fail2ban)",
    "web": "Web server (nginx, ports 80 and 443)",
    "docker": "Docker host (docker, containers, SSH only)",
    "custom": "Custom (I will pick each piece myself)",
}

ROLE_ORDER: list[str] = ["minimal", "web", "docker", "custom"]


class ChooseRoleStep(WizardStep):
    name = "choose_role"
    title = "What is this server for?"

    def run(self, state: WizardState, console: Console) -> None:
        self.render_hint(console, hint("role"))

        labels = [ROLE_LABELS[key] for key in ROLE_ORDER]
        choice = ask_choice(
            "Pick a preset",
            choices=labels,
            console=console,
            default=ROLE_LABELS[state.role] if state.role in ROLE_LABELS else labels[0],
        )

        for key, label in ROLE_LABELS.items():
            if label == choice:
                state.role = key
                break

        self._apply_preset(state)

    def _apply_preset(self, state: WizardState) -> None:
        if state.role == "minimal":
            state.install_nginx = False
            state.install_docker = False
            state.install_fail2ban = True
            state.firewall_allow = [22]
        elif state.role == "web":
            state.install_nginx = True
            state.install_docker = False
            state.install_fail2ban = True
            state.firewall_allow = [22, 80, 443]
        elif state.role == "docker":
            state.install_nginx = False
            state.install_docker = True
            state.install_fail2ban = True
            state.firewall_allow = [22]
        elif state.role == "custom":
            pass
