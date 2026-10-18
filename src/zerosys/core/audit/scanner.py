from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FirewallConfig,
    PackagesConfig,
    ServerConfig,
    ServiceConfig,
    UserConfig,
)


class ConnectionProtocol(Protocol):
    def run(self, command: str, check: bool = False) -> Any: ...
    def read_file(self, path: str) -> str: ...


@dataclass
class AuditResult:
    os_id: str = "unknown"
    packages: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    users: list[str] = field(default_factory=list)
    firewall_ports: list[int] = field(default_factory=list)


class AuditScanner:
    def __init__(self, connection: ConnectionProtocol) -> None:
        self.conn = connection

    def scan(self) -> Config:
        result = AuditResult()

        self._detect_os(result)
        self._detect_packages(result)
        self._detect_services(result)
        self._detect_users(result)
        self._detect_firewall(result)

        return self._build_config(result)

    def _detect_os(self, result: AuditResult) -> None:
        try:
            content = self.conn.read_file("/etc/os-release")
            for line in content.splitlines():
                if line.startswith("ID="):
                    result.os_id = line.split("=")[1].strip("\"'")
                    break
        except Exception:
            pass

    def _detect_packages(self, result: AuditResult) -> None:
        if result.os_id in ("ubuntu", "debian", "linuxmint", "pop"):
            cmd = "apt-mark showmanual 2>/dev/null | head -n 50"
        elif result.os_id in ("arch", "manjaro", "endeavouros"):
            cmd = "pacman -Qe 2>/dev/null | awk '{print $1}' | head -n 50"
        elif result.os_id in ("fedora", "rhel", "centos", "rocky", "almalinux"):
            cmd = "dnf repoquery --userinstalled --qf '%{name}' 2>/dev/null | head -n 50"
        else:
            return

        try:
            output = self.conn.run(cmd).stdout
            if isinstance(output, str):
                pkgs = [line.strip() for line in output.splitlines() if line.strip()]
                result.packages = sorted(set(pkgs))
        except Exception:
            pass

    def _detect_services(self, result: AuditResult) -> None:
        cmd = (
            "systemctl list-units --type=service --state=running "
            "--no-legend --no-pager 2>/dev/null | awk '{print $1}' | "
            "sed 's/.service//' | grep -vE '^(systemd|dbus|cron|ssh|user)' | head -n 20"
        )
        try:
            output = self.conn.run(cmd).stdout
            if isinstance(output, str):
                svcs = [line.strip() for line in output.splitlines() if line.strip()]
                result.services = sorted(set(svcs))
        except Exception:
            pass

    def _detect_users(self, result: AuditResult) -> None:
        cmd = "awk -F: '$3 >= 1000 && $1 != \"nobody\" {print $1}' /etc/passwd 2>/dev/null"
        try:
            output = self.conn.run(cmd).stdout
            if isinstance(output, str):
                users = [line.strip() for line in output.splitlines() if line.strip()]
                result.users = sorted(set(users))
        except Exception:
            pass

    def _detect_firewall(self, result: AuditResult) -> None:
        cmd = "ufw status 2>/dev/null | grep -E '^[0-9]+' | awk '{print $1}' | cut -d'/' -f1"
        try:
            output = self.conn.run(cmd).stdout
            if isinstance(output, str):
                ports = []
                for raw_line in output.splitlines():
                    line = raw_line.strip()
                    if line.isdigit():
                        ports.append(int(line))
                result.firewall_ports = sorted(set(ports))
        except Exception:
            pass

    def _build_config(self, result: AuditResult) -> Config:
        return Config(
            version=CONFIG_VERSION,
            server=ServerConfig(
                hostname="audited-server",
                timezone="UTC",
            ),
            packages=PackagesConfig(
                install=result.packages,
            ),
            services={svc: ServiceConfig(state="started", enabled=True) for svc in result.services},
            users=[UserConfig(name=user, shell="/bin/bash", sudo=True) for user in result.users],
            firewall=FirewallConfig(
                default="deny",
                allow=result.firewall_ports if result.firewall_ports else [22],
            ),
        )
