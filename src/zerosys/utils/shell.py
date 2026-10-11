from __future__ import annotations

import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass

from zerosys.core.errors import ZeroSysError


class ShellError(ZeroSysError):
    pass


DEFAULT_TIMEOUT = 600


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    def __str__(self) -> str:
        return f"{self.command} -> {self.exit_code} ({self.duration_ms} ms)"


def run(
    command: str | list[str],
    timeout: int = DEFAULT_TIMEOUT,
    check: bool = False,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
) -> CommandResult:
    if isinstance(command, list):
        args: str | list[str] = command
        printable = " ".join(shlex.quote(part) for part in command)
    else:
        args = command
        printable = command

    started = time.monotonic()
    try:
        completed = subprocess.run(
            args,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = int((time.monotonic() - started) * 1000)
        raise ShellError(f"command timed out after {timeout}s: {printable}") from exc
    except OSError as exc:
        raise ShellError(f"cannot execute command: {exc}") from exc

    elapsed = int((time.monotonic() - started) * 1000)
    result = CommandResult(
        command=printable,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_ms=elapsed,
    )

    if check and not result.success:
        raise ShellError(f"command failed ({result.exit_code}): {printable}\n{result.stderr}")

    return result


def which(program: str) -> str | None:
    return shutil.which(program)


def has_command(program: str) -> bool:
    return which(program) is not None


def quote(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)
