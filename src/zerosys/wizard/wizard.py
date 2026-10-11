from __future__ import annotations

from pathlib import Path

from rich.console import Console

from zerosys.cli.ui.theme import get_console
from zerosys.core.config.defaults import (
    BASE_PACKAGES_DEBIAN,
    DEFAULT_CONFIG_FILENAME,
)
from zerosys.core.config.parser import write_config
from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FirewallConfig,
    PackagesConfig,
    ServerConfig,
    ServiceConfig,
    UserConfig,
)
from zerosys.wizard.steps.base import WizardState, WizardStep
from zerosys.wizard.steps.choose_role import ChooseRoleStep
from zerosys.wizard.steps.packages import PackagesStep
from zerosys.wizard.steps.review import ReviewStep
from zerosys.wizard.steps.security import SecurityStep
from zerosys.wizard.steps.server_info import ServerInfoStep
from zerosys.wizard.steps.services import ServicesStep
from zerosys.wizard.steps.ssh_setup import SshSetupStep
from zerosys.wizard.steps.welcome import WelcomeStep


class Wizard:
    def __init__(self, steps: list[WizardStep] | None = None) -> None:
        self.steps: list[WizardStep] = steps or [
            WelcomeStep(),
            ServerInfoStep(),
            ChooseRoleStep(),
            SshSetupStep(),
            SecurityStep(),
            ServicesStep(),
            PackagesStep(),
            ReviewStep(),
        ]

    def run(self) -> Config:
        console = get_console()
        state = WizardState()
        total = len(self.steps)

        for index, step in enumerate(self.steps, start=1):
            if step.should_skip(state):
                continue
            step.render_header(console, index, total)
            step.run(state, console)

        return self._build_config(state)

    def _build_config(self, state: WizardState) -> Config:
        install_list: list[str] = list(BASE_PACKAGES_DEBIAN)

        if state.install_nginx:
            install_list.append("nginx")
        if state.install_docker:
            install_list.extend(["docker", "docker-compose"])
        if state.install_fail2ban and "fail2ban" not in install_list:
            install_list.append("fail2ban")

        install_list.extend(p for p in state.extra_packages if p not in install_list)

        services: dict[str, ServiceConfig] = {}
        if state.install_nginx:
            services["nginx"] = ServiceConfig(state="started", enabled=True)
        if state.install_docker:
            services["docker"] = ServiceConfig(state="started", enabled=True)
        if state.install_fail2ban:
            services["fail2ban"] = ServiceConfig(state="started", enabled=True)

        users: list[UserConfig] = []
        if state.admin_user_enabled and state.admin_user_name:
            groups = ["sudo"] if state.admin_user_sudo else []
            user_kwargs: dict[str, object] = {
                "name": state.admin_user_name,
                "groups": groups,
                "shell": "/bin/bash",
                "sudo": state.admin_user_sudo,
            }
            if state.admin_user_ssh_key:
                user_kwargs["ssh_key"] = state.admin_user_ssh_key
            users.append(UserConfig(**user_kwargs))  # type: ignore[arg-type]

        firewall = FirewallConfig(
            default=state.firewall_default,  # type: ignore[arg-type]
            allow=list(state.firewall_allow),
        )

        config_kwargs: dict[str, object] = {
            "version": CONFIG_VERSION,
            "server": ServerConfig(
                hostname=state.hostname,
                timezone=state.timezone,
                locale=state.locale,
            ),
            "packages": PackagesConfig(install=install_list),
            "firewall": firewall,
        }
        if services:
            config_kwargs["services"] = services
        if users:
            config_kwargs["users"] = users

        return Config(**config_kwargs)  # type: ignore[arg-type]


def run_wizard(output: Path | None = None) -> Path:
    console: Console = get_console()
    wizard = Wizard()
    config = wizard.run()
    target = output or Path(DEFAULT_CONFIG_FILENAME)
    path = write_config(config, target)
    console.print(f"[success]Wrote {path}[/success]")
    console.print(f"[hint]Next: 0sys plan {path}[/hint]")
    return path
