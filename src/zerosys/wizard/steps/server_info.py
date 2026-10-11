from __future__ import annotations

import socket

from rich.console import Console

from zerosys.cli.ui.prompts import ask_text
from zerosys.wizard.hints import hint
from zerosys.wizard.steps.base import WizardState, WizardStep


class ServerInfoStep(WizardStep):
    name = "server_info"
    title = "Server identity"

    def _guess_hostname(self) -> str:
        try:
            return socket.gethostname().split(".")[0]
        except OSError:
            return "server"

    def run(self, state: WizardState, console: Console) -> None:
        default_hostname = state.hostname or self._guess_hostname()
        self.render_hint(console, hint("hostname"))
        hostname = ask_text(
            "What should we call this server?",
            console=console,
            default=default_hostname,
        )
        state.hostname = hostname.strip() or default_hostname

        self.render_hint(console, hint("timezone"))
        timezone = ask_text(
            "Which timezone should the server use?",
            console=console,
            default=state.timezone,
        )
        state.timezone = timezone.strip() or "UTC"

        self.render_hint(console, hint("locale"))
        locale = ask_text(
            "Which locale?",
            console=console,
            default=state.locale,
        )
        state.locale = locale.strip() or "en_US.UTF-8"
