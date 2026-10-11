from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from zerosys.core.config.schema import Config

CLOUD_CONFIG_HEADER = "#cloud-config\n"
DEFAULT_OWNER = "root"
DEFAULT_GROUP = "root"


class CloudInitGenerator:
    def generate(self, config: Config) -> str:
        data = self._build_dict(config)
        body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        return CLOUD_CONFIG_HEADER + body

    def _build_dict(self, config: Config) -> dict[str, Any]:
        result: dict[str, Any] = {}
        self._add_server(result, config)
        self._add_packages(result, config)
        self._add_users(result, config)
        self._add_files(result, config)
        self._add_runcmd(result, config)
        return result

    def _add_server(self, result: dict[str, Any], config: Config) -> None:
        if config.server is None:
            return
        if config.server.hostname:
            result["hostname"] = config.server.hostname
            result["preserve_hostname"] = False
        if config.server.timezone:
            result["timezone"] = config.server.timezone
        if config.server.locale:
            result["locale"] = config.server.locale

    def _add_packages(self, result: dict[str, Any], config: Config) -> None:
        if config.packages is None:
            return
        if config.packages.install:
            result["package_update"] = True
            result["packages"] = list(config.packages.install)

    def _add_users(self, result: dict[str, Any], config: Config) -> None:
        if not config.users:
            return
        entries: list[dict[str, Any]] = []
        has_key = False
        for user in config.users:
            entry: dict[str, Any] = {
                "name": user.name,
                "groups": list(user.groups) if user.groups else [],
                "shell": user.shell,
                "lock_passwd": True,
            }
            if user.sudo:
                entry["sudo"] = "ALL=(ALL) NOPASSWD:ALL"
            if user.ssh_key:
                entry["ssh_authorized_keys"] = [user.ssh_key]
                has_key = True
            entries.append(entry)
        result["users"] = entries
        if has_key:
            result["ssh_pwauth"] = False

    def _add_files(self, result: dict[str, Any], config: Config) -> None:
        if not config.files:
            return
        entries: list[dict[str, Any]] = []
        for entry in config.files:
            content = self._read_local_file(entry.src)
            entries.append(
                {
                    "path": entry.dest,
                    "owner": f"{entry.owner or DEFAULT_OWNER}:{entry.group or DEFAULT_GROUP}",
                    "permissions": entry.mode,
                    "content": content,
                }
            )
        result["write_files"] = entries

    def _read_local_file(self, source: str) -> str:
        path = Path(source).expanduser()
        if not path.exists():
            return f"# source not found: {source}\n"
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return f"# cannot read source: {source}\n"

    def _add_runcmd(self, result: dict[str, Any], config: Config) -> None:
        commands: list[str] = []
        commands.extend(self._firewall_commands(config))
        commands.extend(self._service_commands(config))
        commands.extend(self._explicit_commands(config))
        if commands:
            result["runcmd"] = commands

    def _firewall_commands(self, config: Config) -> list[str]:
        if config.firewall is None:
            return []
        lines: list[str] = []
        if config.firewall.default == "deny":
            lines.append("ufw default deny incoming")
            lines.append("ufw default allow outgoing")
        else:
            lines.append("ufw default allow incoming")
            lines.append("ufw default allow outgoing")
        for port in config.firewall.allow:
            lines.append(f"ufw allow {port}/tcp")
        lines.append("ufw --force enable")
        return lines

    def _service_commands(self, config: Config) -> list[str]:
        lines: list[str] = []
        for name, service in config.services.items():
            if service.state == "started" and service.enabled:
                lines.append(f"systemctl enable --now {name}")
            elif service.state == "started":
                lines.append(f"systemctl start {name}")
            elif service.state == "stopped":
                lines.append(f"systemctl stop {name}")
            elif service.state == "restarted":
                lines.append(f"systemctl restart {name}")
            elif service.state == "reloaded":
                lines.append(f"systemctl reload {name}")
        return lines

    def _explicit_commands(self, config: Config) -> list[str]:
        return [entry.run for entry in config.commands]
