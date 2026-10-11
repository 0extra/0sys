from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

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
    ) -> None:
        self.inventory_host = inventory_host
        self.inventory_user = inventory_user
        self.inventory_port = inventory_port
        self.ssh_key = ssh_key
        self.roles_path = roles_path
        self.work_dir = work_dir
        self.verbose = verbose

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
            self._write_inventory(project_dir)
            self._write_playbook(project_dir, playbook)
            self._write_env(project_dir)

            env_vars: dict[str, str] = {}
            if self.ssh_key:
                env_vars["ANSIBLE_PRIVATE_KEY_FILE"] = self.ssh_key

            result = ansible_runner.run(
                private_data_dir=str(project_dir),
                playbook="playbook.yml",
                inventory="inventory.ini",
                extravars=extra_vars or {},
                tags=",".join(tags) if tags else None,
                envvars=env_vars,
                quiet=not self.verbose,
                cmdline="--check" if check else "",
            )

            return self._convert(result)

    def _write_inventory(self, project_dir: Path) -> None:
        host_line = self.inventory_host
        if self.inventory_user:
            host_line = f"{self.inventory_host}"
        lines = ["[all]"]
        entry = host_line
        options: list[str] = []
        if self.inventory_user:
            options.append(f"ansible_user={self.inventory_user}")
        if self.inventory_port != 22:
            options.append(f"ansible_port={self.inventory_port}")
        if self.ssh_key:
            options.append(f"ansible_ssh_private_key_file={self.ssh_key}")
        options.append("ansible_python_interpreter=/usr/bin/python3")
        if options:
            entry = f"{host_line} " + " ".join(options)
        lines.append(entry)
        (project_dir / "inventory.ini").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_playbook(self, project_dir: Path, playbook: list[dict[str, Any]]) -> None:
        content = yaml.safe_dump(playbook, sort_keys=False, allow_unicode=True)
        (project_dir / "playbook.yml").write_text(content, encoding="utf-8")

    def _write_env(self, project_dir: Path) -> None:
        env_dir = project_dir / "env"
        env_dir.mkdir(parents=True, exist_ok=True)
        settings = {
            "host_key_checking": False,
            "retry_files_enabled": False,
            "stdout_callback": "default",
            "gathering": "smart",
        }
        if self.roles_path:
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
