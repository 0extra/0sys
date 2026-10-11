from __future__ import annotations

from pathlib import Path

from rich.console import Console

from zerosys.cli.ui.prompts import ask_confirm, ask_text
from zerosys.wizard.hints import hint
from zerosys.wizard.steps.base import WizardState, WizardStep


class SshSetupStep(WizardStep):
    name = "ssh_setup"
    title = "SSH hardening"

    def _find_default_key(self) -> str | None:
        candidates = [
            Path.home() / ".ssh" / "id_ed25519.pub",
            Path.home() / ".ssh" / "id_rsa.pub",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None

    def run(self, state: WizardState, console: Console) -> None:
        self.render_hint(console, hint("admin_user"))
        create_user = ask_confirm(
            "Create an admin user with sudo access?",
            console=console,
            default=True,
        )

        state.admin_user_enabled = create_user

        if create_user:
            default_name = state.admin_user_name or "admin"
            name = ask_text(
                "Username for the admin account?",
                console=console,
                default=default_name,
            )
            state.admin_user_name = name.strip() or default_name

            self.render_hint(console, hint("ssh_key"))
            default_key = self._find_default_key()
            key_path = ask_text(
                "Path to your public SSH key (leave empty to skip)",
                console=console,
                default=default_key or "",
            )
            key_path = key_path.strip()
            if key_path:
                key_file = Path(key_path).expanduser()
                if key_file.exists():
                    state.admin_user_ssh_key = key_file.read_text(encoding="utf-8").strip()
                    state.add_note(f"SSH key loaded from {key_file}")
                else:
                    console.print(f"[warning]Key file not found: {key_file}[/warning]")
                    state.admin_user_ssh_key = None
            else:
                state.admin_user_ssh_key = None

            state.admin_user_sudo = True

        self.render_hint(console, hint("ssh_hardening"))
        if state.admin_user_ssh_key:
            state.ssh_hardening = ask_confirm(
                "Disable password login? (recommended once your key works)",
                console=console,
                default=True,
            )
        else:
            console.print(
                "[warning]No SSH key provided. Skipping password login hardening.[/warning]"
            )
            state.ssh_hardening = False
