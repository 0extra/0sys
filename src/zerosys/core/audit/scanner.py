from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
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


class DiscoveryStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass
class Discovered:
    values: list[str] = field(default_factory=list)
    status: DiscoveryStatus = DiscoveryStatus.UNSUPPORTED
    detail: str = ""

    def count(self) -> int:
        return len(self.values)


@dataclass
class AuditResult:
    os_id: str = "unknown"
    packages: Discovered = field(default_factory=Discovered)
    services: Discovered = field(default_factory=Discovered)
    users: Discovered = field(default_factory=Discovered)
    firewall_ports: Discovered = field(default_factory=Discovered)
    ufw_active: bool = False
    warnings: list[str] = field(default_factory=list)

    def add_warning(self, text: str) -> None:
        self.warnings.append(text)


_UFW_ANYWHERE_ON_RE = re.compile(r"^Anywhere on (\d+)(?:/(?:tcp|udp))?")
_UFW_PORT_LIST_RE = re.compile(r"^(\d+(?:,\d+)*)(?:/(?:tcp|udp))?")

_DEBIAN_OS_IDS = frozenset({"ubuntu", "debian", "linuxmint", "pop"})
_ARCH_OS_IDS = frozenset({"arch", "manjaro", "endeavouros"})
_REDHAT_OS_IDS = frozenset({"fedora", "rhel", "centos", "rocky", "almalinux"})


def parse_ufw_status(output: str) -> list[int]:
    ports: set[int] = set()
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Status:"):
            continue
        if line.startswith("To "):
            continue
        if line.startswith("--"):
            continue
        anywhere = _UFW_ANYWHERE_ON_RE.match(line)
        if anywhere:
            ports.add(int(anywhere.group(1)))
            continue
        port_list = _UFW_PORT_LIST_RE.match(line)
        if port_list:
            for part in port_list.group(1).split(","):
                if part.isdigit():
                    ports.add(int(part))
    return sorted(ports)


class AuditScanner:
    def __init__(self, connection: ConnectionProtocol) -> None:
        self.conn = connection

    def scan(self) -> tuple[Config, AuditResult]:
        result = AuditResult()
        self._detect_os(result)
        self._detect_packages(result)
        self._detect_services(result)
        self._detect_users(result)
        self._detect_firewall(result)
        config = self._build_config(result)
        return config, result

    def _run(self, command: str) -> Any:
        try:
            return self.conn.run(command)
        except Exception:
            return None

    def _detect_os(self, result: AuditResult) -> None:
        try:
            content = self.conn.read_file("/etc/os-release")
        except Exception:
            return
        for line in content.splitlines():
            if line.startswith("ID="):
                result.os_id = line.split("=", 1)[1].strip("\"'").lower()
                return

    def _detect_packages(self, result: AuditResult) -> None:
        cmd: str | None = None
        if result.os_id in _DEBIAN_OS_IDS:
            cmd = "apt-mark showmanual 2>/dev/null"
        elif result.os_id in _ARCH_OS_IDS:
            cmd = "pacman -Qe 2>/dev/null | awk '{print $1}'"
        elif result.os_id in _REDHAT_OS_IDS:
            cmd = "dnf repoquery --userinstalled --qf '%{name}' 2>/dev/null"

        if cmd is None:
            result.packages = Discovered(
                status=DiscoveryStatus.UNSUPPORTED,
                detail=f"no package manager mapping for os_id={result.os_id}",
            )
            result.add_warning(f"cannot detect packages on os_id={result.os_id}")
            return

        probe = self._run(cmd)
        if probe is None or getattr(probe, "exit_code", 1) != 0:
            result.packages = Discovered(
                status=DiscoveryStatus.FAILED,
                detail="package listing failed",
            )
            result.add_warning("package listing failed; snapshot contains no packages")
            return

        stdout = getattr(probe, "stdout", "") or ""
        pkgs = sorted({line.strip() for line in stdout.splitlines() if line.strip()})
        result.packages = Discovered(
            values=pkgs,
            status=DiscoveryStatus.SUCCESS,
            detail=f"{len(pkgs)} package(s) discovered",
        )
        if len(pkgs) > 500:
            result.add_warning(
                f"package list is large ({len(pkgs)}); consider trimming before apply"
            )

    def _detect_services(self, result: AuditResult) -> None:
        cmd = (
            "systemctl list-units --type=service --state=running "
            "--no-legend --no-pager 2>/dev/null | awk '{print $1}' | "
            "sed 's/.service$//' | grep -vE '^(systemd|dbus|cron|user)'"
        )
        probe = self._run(cmd)
        if probe is None or getattr(probe, "exit_code", 1) != 0:
            result.services = Discovered(
                status=DiscoveryStatus.FAILED,
                detail="systemctl listing failed",
            )
            result.add_warning("service listing failed; snapshot contains no services")
            return
        stdout = getattr(probe, "stdout", "") or ""
        svcs = sorted({line.strip() for line in stdout.splitlines() if line.strip()})
        result.services = Discovered(
            values=svcs,
            status=DiscoveryStatus.SUCCESS,
            detail=f"{len(svcs)} service(s) discovered",
        )
        if len(svcs) > 100:
            result.add_warning(
                f"service list is large ({len(svcs)}); consider trimming before apply"
            )

    def _detect_users(self, result: AuditResult) -> None:
        cmd = "awk -F: '$3 >= 1000 && $1 != \"nobody\" {print $1}' /etc/passwd 2>/dev/null"
        probe = self._run(cmd)
        if probe is None or getattr(probe, "exit_code", 1) != 0:
            result.users = Discovered(
                status=DiscoveryStatus.FAILED,
                detail="user listing failed",
            )
            result.add_warning("user listing failed; snapshot contains no users")
            return
        stdout = getattr(probe, "stdout", "") or ""
        users = sorted({line.strip() for line in stdout.splitlines() if line.strip()})
        result.users = Discovered(
            values=users,
            status=DiscoveryStatus.SUCCESS,
            detail=f"{len(users)} user(s) discovered",
        )

    def _detect_firewall(self, result: AuditResult) -> None:
        ufw_probe = self._run("command -v ufw")
        if ufw_probe is None or getattr(ufw_probe, "exit_code", 1) != 0:
            result.firewall_ports = Discovered(
                status=DiscoveryStatus.UNSUPPORTED,
                detail="ufw is not installed",
            )
            result.add_warning(
                "ufw not found; firewall snapshot defaults to [22] and must be reviewed"
            )
            return

        status_probe = self._run("ufw status 2>/dev/null")
        if status_probe is None or getattr(status_probe, "exit_code", 1) != 0:
            result.firewall_ports = Discovered(
                status=DiscoveryStatus.FAILED,
                detail="ufw status failed",
            )
            result.add_warning(
                "ufw is installed but not readable; firewall snapshot defaults to [22]"
            )
            return

        output = getattr(status_probe, "stdout", "") or ""
        active = "Status: active" in output
        result.ufw_active = active

        if not active:
            result.firewall_ports = Discovered(
                status=DiscoveryStatus.SUCCESS,
                detail="ufw is inactive",
            )
            result.add_warning(
                "ufw is installed but inactive; generated config opens only SSH (22)"
            )
            return

        ports = parse_ufw_status(output)
        if not ports:
            result.firewall_ports = Discovered(
                status=DiscoveryStatus.PARTIAL,
                detail="ufw is active but no port rules were parsed",
            )
            result.add_warning(
                "ufw is active but no ports could be parsed; firewall snapshot defaults to [22]"
            )
            return

        result.firewall_ports = Discovered(
            values=[str(p) for p in ports],
            status=DiscoveryStatus.SUCCESS,
            detail=f"{len(ports)} port(s) discovered",
        )

    def _build_config(self, result: AuditResult) -> Config:
        firewall_allow = [int(p) for p in result.firewall_ports.values if p.isdigit()]
        if not firewall_allow:
            firewall_allow = [22]

        services = {
            name: ServiceConfig(state="started", enabled=True) for name in result.services.values
        }
        users = [
            UserConfig(name=name, shell="/bin/bash", sudo=False) for name in result.users.values
        ]

        return Config(
            version=CONFIG_VERSION,
            server=ServerConfig(hostname="audited-server", timezone="UTC"),
            packages=PackagesConfig(install=list(result.packages.values)),
            services=services,
            users=users,
            firewall=FirewallConfig(default="deny", allow=firewall_allow),
        )
