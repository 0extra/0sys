from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass

from zerosys.core.errors import BackendError


@dataclass
class ShellRunResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def run_local(
    command: str,
    timeout: int = 600,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> ShellRunResult:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = int((time.monotonic() - started) * 1000)
        raise BackendError(f"command timed out after {timeout}s: {command}") from exc
    except OSError as exc:
        raise BackendError(f"failed to execute command: {exc}") from exc

    elapsed = int((time.monotonic() - started) * 1000)
    result = ShellRunResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_ms=elapsed,
    )

    if check and not result.success:
        raise BackendError(
            f"command failed with exit code {result.exit_code}: {command}\n{result.stderr}"
        )

    return result


def run_remote(
    command: str,
    host: str,
    user: str | None = None,
    port: int = 22,
    ssh_key: str | None = None,
    timeout: int = 600,
) -> ShellRunResult:
    target = f"{user}@{host}" if user else host
    ssh_parts = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new"]
    if port != 22:
        ssh_parts += ["-p", str(port)]
    if ssh_key:
        ssh_parts += ["-i", ssh_key]
    ssh_parts.append(target)
    ssh_parts.append(command)

    started = time.monotonic()
    try:
        completed = subprocess.run(
            ssh_parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise BackendError(f"remote command timed out after {timeout}s") from exc
    except OSError as exc:
        raise BackendError(f"failed to execute remote command: {exc}") from exc

    elapsed = int((time.monotonic() - started) * 1000)
    return ShellRunResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_ms=elapsed,
    )


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)
