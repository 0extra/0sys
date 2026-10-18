from __future__ import annotations

from dataclasses import dataclass

import pytest

from zerosys.core.audit import AuditScanner
from zerosys.core.audit.scanner import (
    AuditResult,
    DiscoveryStatus,
    parse_ufw_status,
)
from zerosys.core.config.schema import CONFIG_VERSION

pytestmark = pytest.mark.unit


@dataclass
class _FakeRunResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class _FakeConnection:
    def __init__(
        self,
        commands: dict[str, _FakeRunResult] | None = None,
        os_release: str = "ID=ubuntu\n",
    ) -> None:
        self.commands = commands or {}
        self.os_release = os_release

    def run(self, command: str, check: bool = False) -> _FakeRunResult:
        for key, value in self.commands.items():
            if key in command:
                return value
        return _FakeRunResult(exit_code=1, stderr="not matched")

    def read_file(self, path: str) -> str:
        if path == "/etc/os-release":
            return self.os_release
        raise FileNotFoundError(path)


def _ubuntu_outputs() -> dict[str, _FakeRunResult]:
    return {
        "apt-mark": _FakeRunResult(stdout="nginx\ncurl\nufw\n"),
        "systemctl": _FakeRunResult(stdout="nginx\nfail2ban\n"),
        "/etc/passwd": _FakeRunResult(stdout="deploy\nadmin\n"),
        "command -v ufw": _FakeRunResult(stdout="/usr/sbin/ufw\n"),
        "ufw status": _FakeRunResult(
            stdout=(
                "Status: active\n"
                "\n"
                "To                         Action      From\n"
                "--                         ------      ----\n"
                "22/tcp                     ALLOW       Anywhere\n"
                "80,443/tcp                 ALLOW       Anywhere\n"
                "22/tcp (v6)                ALLOW       Anywhere (v6)\n"
            )
        ),
    }


def test_scan_returns_config_and_result() -> None:
    conn = _FakeConnection(_ubuntu_outputs())
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert config.version == CONFIG_VERSION
    assert isinstance(result, AuditResult)


def test_scan_discovers_packages() -> None:
    conn = _FakeConnection(_ubuntu_outputs())
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.packages.status is DiscoveryStatus.SUCCESS
    assert "nginx" in result.packages.values
    assert "curl" in result.packages.values
    assert config.packages is not None
    assert "nginx" in config.packages.install


def test_scan_discovers_services() -> None:
    conn = _FakeConnection(_ubuntu_outputs())
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.services.status is DiscoveryStatus.SUCCESS
    assert "nginx" in result.services.values
    assert "fail2ban" in config.services


def test_scan_discovers_users_sorted() -> None:
    conn = _FakeConnection(_ubuntu_outputs())
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.users.status is DiscoveryStatus.SUCCESS
    assert result.users.values == ["admin", "deploy"]
    assert [u.name for u in config.users] == ["admin", "deploy"]
    assert all(u.sudo is False for u in config.users)


def test_scan_discovers_firewall_ports() -> None:
    conn = _FakeConnection(_ubuntu_outputs())
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.ufw_active is True
    assert result.firewall_ports.status is DiscoveryStatus.SUCCESS
    assert set(result.firewall_ports.values) == {"22", "80", "443"}
    assert config.firewall is not None
    assert config.firewall.default == "deny"
    assert set(config.firewall.allow) == {22, 80, 443}


def test_scan_empty_server_defaults_to_ssh_only() -> None:
    conn = _FakeConnection(os_release="ID=ubuntu\n")
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert config.packages is not None
    assert config.packages.install == []
    assert config.services == {}
    assert config.users == []
    assert config.firewall is not None
    assert config.firewall.allow == [22]
    assert any("ufw not found" in w for w in result.warnings)


def test_scan_warns_when_ufw_inactive() -> None:
    commands = _ubuntu_outputs()
    commands["ufw status"] = _FakeRunResult(stdout="Status: inactive\n")
    conn = _FakeConnection(commands)
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.ufw_active is False
    assert result.firewall_ports.status is DiscoveryStatus.SUCCESS
    assert config.firewall is not None
    assert config.firewall.allow == [22]
    assert any("inactive" in w for w in result.warnings)


def test_scan_warns_when_ufw_active_but_empty() -> None:
    commands = _ubuntu_outputs()
    commands["ufw status"] = _FakeRunResult(stdout="Status: active\n")
    conn = _FakeConnection(commands)
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.ufw_active is True
    assert result.firewall_ports.status is DiscoveryStatus.PARTIAL
    assert config.firewall is not None
    assert config.firewall.allow == [22]
    assert any("no ports could be parsed" in w for w in result.warnings)


def test_scan_warns_when_packages_fail() -> None:
    commands = _ubuntu_outputs()
    commands["apt-mark"] = _FakeRunResult(exit_code=1, stderr="permission denied")
    conn = _FakeConnection(commands)
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.packages.status is DiscoveryStatus.FAILED
    assert config.packages is not None
    assert config.packages.install == []
    assert any("package listing failed" in w for w in result.warnings)


def test_scan_warns_when_users_fail() -> None:
    commands = _ubuntu_outputs()
    commands["/etc/passwd"] = _FakeRunResult(exit_code=1)
    conn = _FakeConnection(commands)
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.users.status is DiscoveryStatus.FAILED
    assert config.users == []
    assert any("user listing failed" in w for w in result.warnings)


def test_scan_unsupported_os() -> None:
    conn = _FakeConnection(os_release="ID=unknown-os\n")
    scanner = AuditScanner(conn)

    config, result = scanner.scan()

    assert result.packages.status is DiscoveryStatus.UNSUPPORTED
    assert config.packages is not None
    assert config.packages.install == []
    assert any("cannot detect packages" in w for w in result.warnings)


def test_parse_ufw_status_handles_multi_ports() -> None:
    output = (
        "Status: active\n"
        "\n"
        "To                         Action      From\n"
        "--                         ------      ----\n"
        "22/tcp                     ALLOW       Anywhere\n"
        "80,443/tcp                 ALLOW       Anywhere\n"
    )
    assert parse_ufw_status(output) == [22, 80, 443]


def test_parse_ufw_status_handles_anywhere_on() -> None:
    output = (
        "Status: active\n"
        "\n"
        "To                         Action      From\n"
        "--                         ------      ----\n"
        "Anywhere on 22/tcp         ALLOW       Anywhere\n"
        "Anywhere on 51820/udp      ALLOW       Anywhere\n"
    )
    assert parse_ufw_status(output) == [22, 51820]


def test_parse_ufw_status_handles_v6() -> None:
    output = (
        "Status: active\n"
        "\n"
        "To                         Action      From\n"
        "--                         ------      ----\n"
        "22/tcp (v6)                ALLOW       Anywhere (v6)\n"
    )
    assert parse_ufw_status(output) == [22]


def test_parse_ufw_status_inactive() -> None:
    assert parse_ufw_status("Status: inactive\n") == []
