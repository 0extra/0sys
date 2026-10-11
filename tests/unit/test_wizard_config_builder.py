from __future__ import annotations

import pytest

from zerosys.wizard.steps.base import WizardState
from zerosys.wizard.wizard import Wizard

pytestmark = pytest.mark.unit


def _build(state: WizardState):
    wizard = Wizard(steps=[])
    return wizard._build_config(state)


def test_minimal_state_produces_server_and_firewall() -> None:
    state = WizardState()
    state.hostname = "my-vps"
    state.timezone = "UTC"
    state.locale = "en_US.UTF-8"
    state.install_fail2ban = True

    config = _build(state)

    assert config.server is not None
    assert config.server.hostname == "my-vps"
    assert config.firewall is not None
    assert config.firewall.allow == [22]
    assert config.packages is not None
    assert "fail2ban" in config.packages.install
    assert "fail2ban" in config.services
    assert config.users == []


def test_nginx_flag_adds_package_and_service() -> None:
    state = WizardState()
    state.hostname = "web"
    state.install_nginx = True

    config = _build(state)

    assert config.packages is not None
    assert "nginx" in config.packages.install
    assert "nginx" in config.services


def test_docker_flag_adds_packages_and_service() -> None:
    state = WizardState()
    state.hostname = "docker"
    state.install_docker = True

    config = _build(state)

    assert config.packages is not None
    assert "docker" in config.packages.install
    assert "docker-compose" in config.packages.install
    assert "docker" in config.services


def test_extra_packages_are_appended() -> None:
    state = WizardState()
    state.extra_packages = ["htop", "vim"]

    config = _build(state)

    assert config.packages is not None
    assert "htop" in config.packages.install
    assert "vim" in config.packages.install


def test_extra_packages_are_deduplicated() -> None:
    state = WizardState()
    state.extra_packages = ["curl", "htop"]

    config = _build(state)

    assert config.packages is not None
    assert config.packages.install.count("curl") == 1


def test_admin_user_created_when_enabled() -> None:
    state = WizardState()
    state.admin_user_enabled = True
    state.admin_user_name = "admin"
    state.admin_user_sudo = True
    state.admin_user_ssh_key = None

    config = _build(state)

    assert len(config.users) == 1
    user = config.users[0]
    assert user.name == "admin"
    assert "sudo" in user.groups
    assert user.sudo is True
    assert user.ssh_key is None


def test_admin_user_ssh_key_preserved() -> None:
    state = WizardState()
    state.admin_user_enabled = True
    state.admin_user_name = "admin"
    state.admin_user_ssh_key = "ssh-ed25519 AAAA"

    config = _build(state)

    assert config.users[0].ssh_key == "ssh-ed25519 AAAA"


def test_admin_user_without_sudo_has_no_groups() -> None:
    state = WizardState()
    state.admin_user_enabled = True
    state.admin_user_name = "deploy"
    state.admin_user_sudo = False

    config = _build(state)

    assert config.users[0].groups == []
    assert config.users[0].sudo is False


def test_no_admin_user_when_disabled() -> None:
    state = WizardState()
    state.admin_user_enabled = False

    config = _build(state)

    assert config.users == []


def test_no_admin_user_when_name_missing() -> None:
    state = WizardState()
    state.admin_user_enabled = True
    state.admin_user_name = None

    config = _build(state)

    assert config.users == []


def test_services_omitted_when_empty() -> None:
    state = WizardState()
    state.install_fail2ban = False
    state.install_nginx = False
    state.install_docker = False

    config = _build(state)

    assert config.services == {}


def test_firewall_default_allow() -> None:
    state = WizardState()
    state.firewall_default = "allow"

    config = _build(state)

    assert config.firewall is not None
    assert config.firewall.default == "allow"
