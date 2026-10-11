from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from zerosys.core.errors import SecurityError

PRIVATE_MODE = 0o600
PUBLIC_MODE = 0o644
EXECUTABLE_MODE = 0o755


@dataclass(frozen=True)
class PermissionCheck:
    path: str
    expected: int
    actual: int
    ok: bool

    def describe(self) -> str:
        return (
            f"{self.path}: expected {self.expected:o}, "
            f"got {self.actual:o} ({'ok' if self.ok else 'mismatch'})"
        )


def read_mode(path: Path | str) -> int:
    target = Path(path).expanduser()
    if not target.exists():
        raise SecurityError(f"file not found: {target}")
    return target.stat().st_mode & 0o777


def set_mode(path: Path | str, mode: int) -> None:
    target = Path(path).expanduser()
    if not target.exists():
        raise SecurityError(f"file not found: {target}")
    if mode < 0 or mode > 0o777:
        raise SecurityError(f"invalid mode: {mode:o}")
    target.chmod(mode)


def check_mode(path: Path | str, expected: int) -> PermissionCheck:
    target = Path(path).expanduser()
    actual = read_mode(target)
    return PermissionCheck(
        path=str(target),
        expected=expected,
        actual=actual,
        ok=actual == expected,
    )


def is_world_readable(path: Path | str) -> bool:
    return bool(read_mode(path) & stat.S_IROTH)


def is_world_writable(path: Path | str) -> bool:
    return bool(read_mode(path) & stat.S_IWOTH)


def is_group_writable(path: Path | str) -> bool:
    return bool(read_mode(path) & stat.S_IWGRP)


def is_owned_by_current_user(path: Path | str) -> bool:
    target = Path(path).expanduser()
    if not target.exists():
        raise SecurityError(f"file not found: {target}")
    try:
        return target.stat().st_uid == os.getuid()
    except OSError:
        return False


def ensure_secure_file(path: Path | str, mode: int = PRIVATE_MODE) -> None:
    target = Path(path).expanduser()
    if not target.exists():
        raise SecurityError(f"file not found: {target}")
    current = read_mode(target)
    if current != mode:
        target.chmod(mode)


def is_insecure(path: Path | str) -> bool:
    mode = read_mode(path)
    if mode & stat.S_IWOTH:
        return True
    return bool(mode & stat.S_IWGRP)
