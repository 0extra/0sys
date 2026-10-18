from __future__ import annotations

from dataclasses import dataclass

import pytest

from zerosys.core.audit import AuditScanner
from zerosys.core.config.schema import CONFIG_VERSION

pytestmark = pytest.mark.unit


@dataclass
class _FakeRunResult:
    stdout: str


class _FakeConnection:
    def __init__(self, outputs: dict[str, str]) -> None:
        self.outputs = outputs

    def run(self, command: str, check: bool = False) -> _FakeRunResult:
        for key, value in self.outputs.items():
            if key in command:
                return _FakeRunResult(stdout=value)
        return _FakeRunResult(stdout="")

    def read_file(self, path: str) -> str:
        if path == "/etc/os-release":
            return 'ID=ubuntu\nVERSION_ID="22.04"\n'
        return ""


def test_audit_scanner_builds_config() -> None:
    outputs = {
        "apt-mark": "nginx\ncurl\nufw\n",
        "systemctl": "nginx\nfail2ban\n",
        "/etc/passwd": "deploy\nadmin\n",
        "ufw status": "22\n80\n443\n",
    }
    conn = _FakeConnection(outputs)
    scanner = AuditScanner(conn)  # type: ignore[arg-type]

    config = scanner.scan()

    assert config.version == CONFIG_VERSION
    assert config.server is not None
    assert config.packages is not None
    assert "nginx" in config.packages.install
    assert "curl" in config.packages.install
    assert "nginx" in config.services
    assert "fail2ban" in config.services

    assert len(config.users) == 2
    assert config.users[0].name == "admin"
    assert config.users[1].name == "deploy"

    assert config.firewall is not None
    assert 22 in config.firewall.allow
    assert 80 in config.firewall.allow


def test_audit_scanner_handles_empty_server() -> None:
    conn = _FakeConnection({})
    scanner = AuditScanner(conn)  # type: ignore[arg-type]

    config = scanner.scan()

    assert config.version == CONFIG_VERSION
    assert config.packages is not None
    assert len(config.packages.install) == 0
    assert len(config.services) == 0
    assert len(config.users) == 0
    assert config.firewall is not None
    assert config.firewall.allow == [22]
