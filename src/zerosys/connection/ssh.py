from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from zerosys.core.errors import ZeroSysError
from zerosys.core.security.ssh import check_private_key_permissions

DEFAULT_TIMEOUT = 600
SSH_PORT_DEFAULT = 22


class ConnectionError(ZeroSysError):
    pass


@dataclass(frozen=True)
class ConnectionResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class SshConnection:
    name = "ssh"

    def __init__(
        self,
        host: str,
        user: str | None = None,
        port: int = SSH_PORT_DEFAULT,
        key_file: Path | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        strict_host_key: bool = False,
    ) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.key_file = Path(key_file).expanduser() if key_file else None
        self.timeout = timeout
        self.strict_host_key = strict_host_key

    def _target(self) -> str:
        if self.user:
            return f"{self.user}@{self.host}"
        return self.host

    def _build_ssh_argv(self, command: str) -> list[str]:
        argv = ["ssh"]
        if not self.strict_host_key:
            argv.extend(["-o", "StrictHostKeyChecking=accept-new"])
        argv.extend(["-o", "BatchMode=yes"])
        argv.extend(["-o", f"ConnectTimeout={min(self.timeout, 30)}"])
        if self.port != SSH_PORT_DEFAULT:
            argv.extend(["-p", str(self.port)])
        if self.key_file is not None:
            argv.extend(["-i", str(self.key_file)])
        argv.append(self._target())
        argv.append(command)
        return argv

    def run(self, command: str, check: bool = False) -> ConnectionResult:
        argv = self._build_ssh_argv(command)
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ConnectionError(f"SSH command timed out: {command}") from exc
        except OSError as exc:
            raise ConnectionError(f"cannot spawn ssh: {exc}") from exc

        elapsed = int((time.monotonic() - started) * 1000)
        result = ConnectionResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_ms=elapsed,
        )
        if check and not result.success:
            raise ConnectionError(
                f"SSH command failed ({result.exit_code}): {command}\n{result.stderr}"
            )
        return result

    def test(self) -> bool:
        return self.run("true").success

    def exists(self, path: str) -> bool:
        return self.run(f"test -e {shlex.quote(path)}").success

    def read_file(self, path: str) -> str:
        return self.run(f"cat {shlex.quote(path)}", check=True).stdout

    def write_file(self, path: str, content: str) -> None:
        escaped = shlex.quote(content)
        self.run(f"printf %s {escaped} > {shlex.quote(path)}", check=True)

    def copy_to(self, local: Path, remote: str) -> None:
        source = Path(local).expanduser().resolve()
        if not source.exists():
            raise ConnectionError(f"local file not found: {source}")
        argv = ["scp"]
        if not self.strict_host_key:
            argv.extend(["-o", "StrictHostKeyChecking=accept-new"])
        argv.extend(["-o", "BatchMode=yes"])
        if self.port != SSH_PORT_DEFAULT:
            argv.extend(["-P", str(self.port)])
        if self.key_file is not None:
            argv.extend(["-i", str(self.key_file)])
        argv.append(str(source))
        argv.append(f"{self._target()}:{remote}")

        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except OSError as exc:
            raise ConnectionError(f"cannot spawn scp: {exc}") from exc

        if completed.returncode != 0:
            raise ConnectionError(f"scp failed: {completed.stderr.strip()}")

    def check_key_permissions(self) -> bool:
        if self.key_file is None:
            return True
        result = check_private_key_permissions(self.key_file)
        return bool(result)

    def close(self) -> None:
        return None

    def describe(self) -> str:
        port_part = f":{self.port}" if self.port != SSH_PORT_DEFAULT else ""
        key_part = f" (key={self.key_file})" if self.key_file else ""
        return f"ssh://{self._target()}{port_part}{key_part}"
