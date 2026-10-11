from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass

from zerosys.core.errors import ZeroSysError

DEFAULT_TIMEOUT = 600


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


class LocalConnection:
    name = "local"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout

    def run(self, command: str, check: bool = False) -> ConnectionResult:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ConnectionError(f"command timed out: {command}") from exc
        except OSError as exc:
            raise ConnectionError(f"cannot execute: {exc}") from exc

        elapsed = int((time.monotonic() - started) * 1000)
        result = ConnectionResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_ms=elapsed,
        )
        if check and not result.success:
            raise ConnectionError(f"command failed: {command}\n{result.stderr}")
        return result

    def run_argv(self, argv: list[str], check: bool = False) -> ConnectionResult:
        return self.run(shlex.join(argv), check=check)

    def exists(self, path: str) -> bool:
        result = self.run(f"test -e {shlex.quote(path)}")
        return result.success

    def read_file(self, path: str) -> str:
        result = self.run(f"cat {shlex.quote(path)}", check=True)
        return result.stdout

    def write_file(self, path: str, content: str) -> None:
        escaped = shlex.quote(content)
        self.run(f"printf %s {escaped} > {shlex.quote(path)}", check=True)

    def close(self) -> None:
        return None
