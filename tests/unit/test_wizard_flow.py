from __future__ import annotations

from unittest.mock import patch

import pytest

from zerosys.wizard.wizard import Wizard

pytestmark = pytest.mark.unit


@patch("zerosys.wizard.steps.server_info.ask_text")
@patch("zerosys.wizard.steps.choose_role.ask_choice")
@patch("zerosys.wizard.steps.ssh_setup.ask_confirm")
@patch("zerosys.wizard.steps.ssh_setup.ask_text")
@patch("zerosys.wizard.steps.security.ask_confirm")
@patch("zerosys.wizard.steps.security.ask_multi_choice")
@patch("zerosys.wizard.steps.services.ask_confirm")
@patch("zerosys.wizard.steps.packages.ask_text")
@patch("zerosys.wizard.steps.review.ask_confirm")
def test_wizard_full_run(
    mock_review_confirm,
    mock_pkg_text,
    mock_svc_confirm,
    mock_sec_multi,
    mock_sec_confirm,
    mock_ssh_text,
    mock_ssh_confirm,
    mock_role_choice,
    mock_srv_text,
):
    mock_srv_text.side_effect = ["test-host", "UTC", "en_US.UTF-8"]
    mock_role_choice.return_value = "Web server (nginx, ports 80 and 443)"
    mock_ssh_confirm.side_effect = [True, True]
    mock_ssh_text.side_effect = ["admin", ""]
    mock_sec_confirm.return_value = True
    mock_sec_multi.return_value = [
        "SSH (22) - you need this to log in",
        "HTTP (80) - unencrypted web",
    ]
    mock_svc_confirm.side_effect = [True, False]
    mock_pkg_text.return_value = "vim, htop"
    mock_review_confirm.return_value = True

    wizard = Wizard()
    config = wizard.run()

    assert config.server is not None
    assert config.server.hostname == "test-host"
    assert config.server.timezone == "UTC"
    assert config.firewall is not None
    assert 80 in config.firewall.allow
    assert config.packages is not None
    assert "nginx" in config.packages.install
    assert "vim" in config.packages.install
    assert "htop" in config.packages.install
    assert len(config.users) == 1
    assert config.users[0].name == "admin"
