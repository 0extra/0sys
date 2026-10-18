from __future__ import annotations

import contextlib
import json
import shlex
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from platformdirs import user_data_dir

from zerosys.core.errors import BackendError


@dataclass
class AnsibleRunResult:
    success: bool
    status: str
    stdout: str = ""
    stderr: str = ""
    stats: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0


class AnsibleRunner:
    def __init__(
        self,
        inventory_host: str,
        inventory_user: str | None = None,
        inventory_port: int = 22,
        ssh_key: str | None = None,
        roles_path: Path | None = None,
        work_dir: Path | None = None,
        verbose: bool = False,
        known_hosts_file: Path | None = None,
        strict_host_key: bool = False,
    ) -> None:
        self.inventory_host = inventory_host
        self.inventory_user = inventory_user
        self.inventory_port = inventory_port
        self.ssh_key = ssh_key
        self.roles_path = roles_path
        self.work_dir = work_dir
        self.verbose = verbose
        self.known_hosts_file = known_hosts_file
        self.strict_host_key = strict_host_key

    def run(
        self,
        playbook: list[dict[str, Any]],
        extra_vars: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        check: bool = False,
    ) -> AnsibleRunResult:
        try:
            import ansible_runner
        except ImportError as exc:
            raise BackendError(
                "ansible-runner is not installed; install zerosys with ansible support"
            ) from exc

        with tempfile.TemporaryDirectory(prefix="0sys-ansible-") as tmp:
            project_dir = Path(tmp)
            self._write_playbook(project_dir, playbook)
            self._copy_roles(project_dir)
            self._write_env(project_dir)

            env_vars: dict[str, str] = {}
            if self.ssh_key:
                env_vars["ANSIBLE_PRIVATE_KEY_FILE"] = self.ssh_key
            if self.roles_path and self.roles_path.exists():
                env_vars["ANSIBLE_ROLES_PATH"] = str(self.roles_path)

            result = ansible_runner.run(
                private_data_dir=str(project_dir),
                playbook="playbook.yml",
                inventory=self._build_inventory(),
                extravars=extra_vars or {},
                tags=",".join(tags) if tags else None,
                envvars=env_vars,
                quiet=not self.verbose,
                cmdline="--check" if check else "",
            )

            return self._convert(result)

    def _build_inventory(self) -> dict[str, Any]:
        is_local = self.inventory_host in ("localhost", "127.0.0.1", "::1")
        host_vars: dict[str, Any] = {}

        if is_local:
            host_vars["ansible_connection"] = "local"
            host_vars["ansible_python_interpreter"] = sys.executable
        else:
            if self.inventory_user:
                host_vars["ansible_user"] = self.inventory_user
            if self.inventory_port != 22:
                host_vars["ansible_port"] = self.inventory_port
            if self.ssh_key:
                host_vars["ansible_ssh_private_key_file"] = self.ssh_key
            host_vars["ansible_python_interpreter"] = "auto_silent"

            known_hosts = self.known_hosts_file or (
                Path(user_data_dir("0sys", "0extra")) / "known_hosts"
            )
            with contextlib.suppress(OSError):
                known_hosts.parent.mkdir(parents=True, exist_ok=True)

            check_mode = "yes" if self.strict_host_key else "accept-new"
            host_vars["ansible_ssh_common_args"] = (
                f"-o StrictHostKeyChecking={check_mode} "
                f"-o UserKnownHostsFile={shlex.quote(str(known_hosts))}"
            )

        return {
            "all": {
                "hosts": {
                    self.inventory_host: host_vars,
                }
            }
        }

    def _copy_roles(self, project_dir: Path) -> None:
        if self.roles_path is None or not self.roles_path.exists():
            return
        target = project_dir / "roles"
        shutil.copytree(self.roles_path, target, dirs_exist_ok=True)

    def _write_playbook(self, project_dir: Path, playbook: list[dict[str, Any]]) -> None:
        content = yaml.safe_dump(playbook, sort_keys=False, allow_unicode=True)
        (project_dir / "playbook.yml").write_text(content, encoding="utf-8")

    def _write_env(self, project_dir: Path) -> None:
        env_dir = project_dir / "env"
        env_dir.mkdir(parents=True, exist_ok=True)
        settings: dict[str, Any] = {
            "host_key_checking": self.strict_host_key,
            "retry_files_enabled": False,
            "stdout_callback": "default",
            "gathering": "smart",
        }
        if self.roles_path and self.roles_path.exists():
            settings["roles_path"] = str(self.roles_path)
        (env_dir / "settings").write_text(json.dumps(settings, indent=2), encoding="utf-8")

    def _convert(self, result: Any) -> AnsibleRunResult:
        status = result.status
        success = status == "successful"
        stdout = ""
        stderr = ""
        stats: dict[str, Any] = {}

        try:
            stdout = (
                result.stdout.read() if hasattr(result.stdout, "read") else str(result.stdout or "")
            )
        except Exception:
            stdout = ""

        try:
            stderr = (
                result.stderr.read() if hasattr(result.stderr, "read") else str(result.stderr or "")
            )
        except Exception:
            stderr = ""

        if hasattr(result, "stats"):
            stats = dict(result.stats or {})

        return AnsibleRunResult(
            success=success,
            status=status,
            stdout=stdout,
            stderr=stderr,
            stats=stats,
        )
