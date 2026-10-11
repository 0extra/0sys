from __future__ import annotations

import pytest

from zerosys.wizard.steps.base import WizardState, WizardStep

pytestmark = pytest.mark.unit


def test_default_state() -> None:
    state = WizardState()

    assert state.hostname is None
    assert state.timezone == "UTC"
    assert state.locale == "en_US.UTF-8"
    assert state.role == "minimal"
    assert state.admin_user_enabled is False
    assert state.firewall_default == "deny"
    assert state.firewall_allow == [22]
    assert state.install_nginx is False
    assert state.install_docker is False
    assert state.install_fail2ban is False
    assert state.extra_packages == []
    assert state.notes == []


def test_add_note_appends() -> None:
    state = WizardState()
    state.add_note("first")
    state.add_note("second")

    assert state.notes == ["first", "second"]


def test_as_summary_contains_all_keys() -> None:
    state = WizardState()
    summary = state.as_summary()

    expected_keys = {
        "hostname",
        "timezone",
        "locale",
        "role",
        "admin user",
        "ssh hardening",
        "firewall default",
        "firewall allow",
        "nginx",
        "docker",
        "fail2ban",
        "extra packages",
    }

    assert set(summary.keys()) == expected_keys


def test_as_summary_hostname_placeholder() -> None:
    state = WizardState()

    assert state.as_summary()["hostname"] == "(unchanged)"


def test_as_summary_admin_user_disabled() -> None:
    state = WizardState()

    assert state.as_summary()["admin user"] == "not created"


def test_as_summary_admin_user_enabled() -> None:
    state = WizardState()
    state.admin_user_enabled = True
    state.admin_user_name = "deploy"
    state.admin_user_sudo = True

    assert "deploy" in state.as_summary()["admin user"]


def test_as_summary_firewall_allow_format() -> None:
    state = WizardState()
    state.firewall_allow = [22, 80, 443]

    assert state.as_summary()["firewall allow"] == "22, 80, 443"


def test_as_summary_extra_packages() -> None:
    state = WizardState()
    state.extra_packages = ["htop", "vim"]

    assert state.as_summary()["extra packages"] == "htop, vim"


class _DummyStep(WizardStep):
    name = "dummy"
    title = "Dummy"

    def run(self, state: WizardState, console) -> None:
        state.add_note("ran")


def test_wizard_step_default_should_skip() -> None:
    step = _DummyStep()

    assert step.should_skip(WizardState()) is False
