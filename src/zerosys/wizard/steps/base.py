from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


@dataclass
class WizardState:
    hostname: str | None = None
    timezone: str = "UTC"
    locale: str = "en_US.UTF-8"

    role: str = "minimal"

    admin_user_enabled: bool = False
    admin_user_name: str | None = None
    admin_user_ssh_key: str | None = None
    admin_user_sudo: bool = True

    ssh_hardening: bool = False

    firewall_default: str = "deny"
    firewall_allow: list[int] = field(default_factory=lambda: [22])

    install_nginx: bool = False
    install_docker: bool = False
    install_fail2ban: bool = False

    extra_packages: list[str] = field(default_factory=list)

    notes: list[str] = field(default_factory=list)

    def add_note(self, text: str) -> None:
        self.notes.append(text)

    def as_summary(self) -> dict[str, Any]:
        return {
            "hostname": self.hostname or "(unchanged)",
            "timezone": self.timezone,
            "locale": self.locale,
            "role": self.role,
            "admin user": (
                f"{self.admin_user_name} (sudo={self.admin_user_sudo})"
                if self.admin_user_enabled and self.admin_user_name
                else "not created"
            ),
            "ssh hardening": "on" if self.ssh_hardening else "off",
            "firewall default": self.firewall_default,
            "firewall allow": ", ".join(str(p) for p in self.firewall_allow) or "(none)",
            "nginx": "yes" if self.install_nginx else "no",
            "docker": "yes" if self.install_docker else "no",
            "fail2ban": "yes" if self.install_fail2ban else "no",
            "extra packages": (", ".join(self.extra_packages) if self.extra_packages else "(none)"),
        }


class WizardStep(ABC):
    name: str = "step"
    title: str = "Step"

    @abstractmethod
    def run(self, state: WizardState, console: Console) -> None: ...

    def should_skip(self, state: WizardState) -> bool:
        return False

    def render_header(self, console: Console, index: int, total: int) -> None:
        header = Text()
        header.append(f"Step {index}/{total}", style="accent")
        header.append("  ")
        header.append(self.title, style="primary")
        console.print()
        console.print(Panel(header, border_style="primary", padding=(0, 2)))

    def render_hint(self, console: Console, text: str) -> None:
        if not text:
            return
        console.print(Text(f"  hint: {text}", style="hint"))
