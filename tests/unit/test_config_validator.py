from __future__ import annotations

import pytest

from zerosys.core.config.schema import (
    CONFIG_VERSION,
    CommandEntry,
    Config,
    FileEntry,
    FirewallConfig,
    PackagesConfig,
    ServerConfig,
    ServiceConfig,
    UserConfig,
)
from zerosys.core.config.validator import Severity, validate

pytestmark = pytest.mark.unit


def test_fw001_firewall_deny_without_ssh() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[80]),
    )

    report = validate(config)

    assert "FW001" in {i.code for i in report.issues}
    assert report.has_errors


def test_fw001_not_triggered_when_ssh_allowed() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22]),
    )

    report = validate(config)

    assert "FW001" not in {i.code for i in report.issues}


def test_fw001_respects_custom_ssh_port() -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="web", ssh_port=2222),
        firewall=FirewallConfig(default="deny", allow=[2222]),
    )

    report = validate(config)

    assert "FW001" not in {i.code for i in report.issues}


def test_fw001_triggers_when_custom_ssh_port_missing() -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="web", ssh_port=2222),
        firewall=FirewallConfig(default="deny", allow=[22]),
    )

    report = validate(config)

    assert "FW001" in {i.code for i in report.issues}
    message = next(i.message for i in report.issues if i.code == "FW001")
    assert "2222" in message


def test_fw002_firewall_allow_default_warns() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="allow", allow=[22]),
    )

    report = validate(config)

    assert "FW002" in {i.code for i in report.issues}
    assert report.has_warnings


def test_fw003_does_not_warn_on_custom_ssh_port() -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(ssh_port=2222),
        firewall=FirewallConfig(default="deny", allow=[2222]),
    )

    report = validate(config)

    infos = {i.code for i in report.infos()}
    assert "FW003" not in infos


def test_fw004_nginx_without_http_ports() -> None:
    config = Config(
        version=CONFIG_VERSION,
        services={"nginx": ServiceConfig()},
        firewall=FirewallConfig(default="deny", allow=[22]),
    )

    report = validate(config)

    assert "FW004" in {i.code for i in report.issues}


def test_usr001_no_sudo_user_warns() -> None:
    config = Config(
        version=CONFIG_VERSION,
        users=[UserConfig(name="alice", groups=[], shell="/bin/bash")],
    )

    report = validate(config)

    assert "USR001" in {i.code for i in report.issues}


def test_usr002_sudo_with_nologin_shell_errors() -> None:
    config = Config(
        version=CONFIG_VERSION,
        users=[
            UserConfig(
                name="ghost",
                groups=["sudo"],
                shell="/usr/sbin/nologin",
                sudo=True,
            )
        ],
    )

    report = validate(config)

    assert "USR002" in {i.code for i in report.issues}
    assert report.has_errors


def test_usr003_user_without_ssh_key_is_info() -> None:
    config = Config(
        version=CONFIG_VERSION,
        users=[UserConfig(name="bob", groups=["sudo"], sudo=True)],
    )

    report = validate(config)

    infos = {i.code for i in report.infos()}
    assert "USR003" in infos


def test_pkg001_install_and_remove_same_package() -> None:
    config = Config(
        version=CONFIG_VERSION,
        packages=PackagesConfig(install=["nginx"], remove=["nginx"]),
    )

    report = validate(config)

    assert "PKG001" in {i.code for i in report.issues}
    assert report.has_errors


def test_file001_relative_destination() -> None:
    config = Config(
        version=CONFIG_VERSION,
        files=[FileEntry(src="./x", dest="relative/path")],
    )

    report = validate(config)

    assert "FILE001" in {i.code for i in report.issues}


def test_cmd001_duplicate_command_name() -> None:
    config = Config(
        version=CONFIG_VERSION,
        commands=[
            CommandEntry(name="deploy", run="echo 1"),
            CommandEntry(name="deploy", run="echo 2"),
        ],
    )

    report = validate(config)

    warnings = {i.code for i in report.warnings()}
    assert "CMD001" in warnings


def test_srv001_missing_hostname_is_info() -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(timezone="UTC"),
    )

    report = validate(config)

    assert "SRV001" in {i.code for i in report.infos()}


def test_clean_config_has_no_errors() -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="ok"),
        firewall=FirewallConfig(default="deny", allow=[22]),
    )

    report = validate(config)

    assert not report.has_errors


def test_issue_str_includes_code_and_path() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[80]),
    )

    report = validate(config)
    errors = report.errors()

    assert errors
    assert "FW001" in str(errors[0])
    assert "firewall.allow" in str(errors[0])
    assert errors[0].severity is Severity.ERROR
