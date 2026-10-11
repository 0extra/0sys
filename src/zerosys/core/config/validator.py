from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from zerosys.core.config.schema import Config


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationIssue:
    severity: Severity
    code: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        location = f" [{self.path}]" if self.path else ""
        return f"{self.severity.value.upper()}: {self.code}{location}: {self.message}"


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity is Severity.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.severity is Severity.WARNING for issue in self.issues)

    def add(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity is Severity.ERROR]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity is Severity.WARNING]

    def infos(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity is Severity.INFO]


SSH_DEFAULT_PORT = 22
DANGEROUS_SHELLS = {"/sbin/nologin", "/usr/sbin/nologin", "/bin/false"}
PRIVILEGED_PORTS = {22, 80, 443, 3306, 5432, 6379, 27017}
COMMON_SERVICES = {
    "nginx": {80, 443},
    "apache2": {80, 443},
    "httpd": {80, 443},
    "mysql": {3306},
    "mariadb": {3306},
    "postgresql": {5432},
    "redis": {6379},
    "redis-server": {6379},
    "mongodb": {27017},
    "sshd": {22},
    "ssh": {22},
}


def validate(config: Config) -> ValidationReport:
    report = ValidationReport()

    _check_firewall_ssh_lockout(config, report)
    _check_firewall_defaults(config, report)
    _check_services_without_firewall_ports(config, report)
    _check_users(config, report)
    _check_packages_conflicts(config, report)
    _check_files(config, report)
    _check_commands(config, report)
    _check_server(config, report)
    _check_proxy_port(config, report)

    return report


def _check_firewall_ssh_lockout(config: Config, report: ValidationReport) -> None:
    if config.firewall is None:
        return
    if config.firewall.default == "allow":
        return
    if SSH_DEFAULT_PORT not in config.firewall.allow:
        report.add(
            ValidationIssue(
                severity=Severity.ERROR,
                code="FW001",
                message=(
                    "firewall default is deny but port 22 is not allowed; "
                    "this will lock you out of the server"
                ),
                path="firewall.allow",
            )
        )


def _check_firewall_defaults(config: Config, report: ValidationReport) -> None:
    if config.firewall is None:
        return
    if config.firewall.default == "allow":
        report.add(
            ValidationIssue(
                severity=Severity.WARNING,
                code="FW002",
                message=(
                    "firewall default is allow; every port on the server is open to the internet"
                ),
                path="firewall.default",
            )
        )
    for port in config.firewall.allow:
        if port in PRIVILEGED_PORTS and port != SSH_DEFAULT_PORT:
            report.add(
                ValidationIssue(
                    severity=Severity.INFO,
                    code="FW003",
                    message=f"port {port} is a well-known service port; make sure it is intended",
                    path="firewall.allow",
                )
            )


def _check_services_without_firewall_ports(config: Config, report: ValidationReport) -> None:
    if config.firewall is None:
        return
    allowed = set(config.firewall.allow)
    for service_name in config.services:
        expected_ports = COMMON_SERVICES.get(service_name)
        if not expected_ports:
            continue
        missing = expected_ports - allowed
        if missing and config.firewall.default == "deny":
            report.add(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="FW004",
                    message=(
                        f"service '{service_name}' usually needs ports "
                        f"{sorted(expected_ports)} but firewall only allows {sorted(allowed)}"
                    ),
                    path=f"services.{service_name}",
                )
            )


def _check_users(config: Config, report: ValidationReport) -> None:
    if not config.users:
        return
    has_admin = any(user.sudo or "sudo" in user.groups for user in config.users)
    if not has_admin:
        report.add(
            ValidationIssue(
                severity=Severity.WARNING,
                code="USR001",
                message="no user has sudo access; you may not be able to administer the server",
                path="users",
            )
        )
    for user in config.users:
        if user.shell in DANGEROUS_SHELLS and user.sudo:
            report.add(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="USR002",
                    message=f"user '{user.name}' has sudo but shell '{user.shell}' cannot log in",
                    path=f"users.{user.name}",
                )
            )
        if user.ssh_key is None and user.shell not in DANGEROUS_SHELLS:
            report.add(
                ValidationIssue(
                    severity=Severity.INFO,
                    code="USR003",
                    message=f"user '{user.name}' has no ssh key; login will require a password",
                    path=f"users.{user.name}",
                )
            )


def _check_packages_conflicts(config: Config, report: ValidationReport) -> None:
    if config.packages is None:
        return
    install_set = set(config.packages.install)
    remove_set = set(config.packages.remove)
    conflicts = install_set & remove_set
    for name in sorted(conflicts):
        report.add(
            ValidationIssue(
                severity=Severity.ERROR,
                code="PKG001",
                message=f"package '{name}' is listed in both install and remove",
                path="packages",
            )
        )


def _check_files(config: Config, report: ValidationReport) -> None:
    for entry in config.files:
        if not entry.dest.startswith("/"):
            report.add(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="FILE001",
                    message=f"destination '{entry.dest}' must be an absolute path",
                    path=f"files.{entry.dest}",
                )
            )


def _check_commands(config: Config, report: ValidationReport) -> None:
    seen_names: set[str] = set()
    for entry in config.commands:
        if entry.name in seen_names:
            report.add(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="CMD001",
                    message=f"duplicate command name '{entry.name}'",
                    path=f"commands.{entry.name}",
                )
            )
        seen_names.add(entry.name)


def _check_server(config: Config, report: ValidationReport) -> None:
    if config.server is None:
        return
    if config.server.hostname is None:
        report.add(
            ValidationIssue(
                severity=Severity.INFO,
                code="SRV001",
                message="server hostname is not set; the default hostname will be kept",
                path="server.hostname",
            )
        )


def _check_proxy_port(config: Config, report: ValidationReport) -> None:
    if config.proxy is None or not config.proxy.enabled:
        return
    if config.firewall is None:
        return
    if config.firewall.default != "deny":
        return
    if config.proxy.port not in config.firewall.allow:
        report.add(
            ValidationIssue(
                severity=Severity.WARNING,
                code="PROXY001",
                message=(
                    f"proxy is enabled and uses port {config.proxy.port}, "
                    f"but firewall does not allow it; clients will not connect"
                ),
                path="proxy.port",
            )
        )
