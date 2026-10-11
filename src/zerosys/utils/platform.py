from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class OSFamily(StrEnum):
    DEBIAN = "debian"
    REDHAT = "redhat"
    ARCH = "arch"
    ALPINE = "alpine"
    SUSE = "suse"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PlatformInfo:
    system: str
    machine: str
    release: str
    family: OSFamily
    is_linux: bool
    is_macos: bool
    is_windows: bool
    is_wsl: bool


OS_RELEASE_PATH = Path("/etc/os-release")
PROC_VERSION_PATH = Path("/proc/version")


def _read_os_release() -> dict[str, str]:
    if not OS_RELEASE_PATH.exists():
        return {}
    result: dict[str, str] = {}
    try:
        content = OS_RELEASE_PATH.read_text(encoding="utf-8")
    except OSError:
        return {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        value = value.strip().strip('"').strip("'")
        result[key.strip()] = value
    return result


def _detect_family() -> OSFamily:
    data = _read_os_release()
    id_like = data.get("ID_LIKE", "").lower()
    os_id = data.get("ID", "").lower()
    combined = f"{os_id} {id_like}"

    if any(token in combined for token in ("debian", "ubuntu", "mint", "pop")):
        return OSFamily.DEBIAN
    if any(token in combined for token in ("rhel", "fedora", "centos", "rocky", "almalinux")):
        return OSFamily.REDHAT
    if "arch" in combined or os_id in {"arch", "manjaro", "endeavouros"}:
        return OSFamily.ARCH
    if "alpine" in combined:
        return OSFamily.ALPINE
    if "suse" in combined or "opensuse" in combined:
        return OSFamily.SUSE
    return OSFamily.UNKNOWN


def _detect_wsl() -> bool:
    if not PROC_VERSION_PATH.exists():
        return False
    try:
        content = PROC_VERSION_PATH.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return "microsoft" in content or "wsl" in content


def detect_platform() -> PlatformInfo:
    system = platform.system().lower()
    return PlatformInfo(
        system=system,
        machine=platform.machine(),
        release=platform.release(),
        family=_detect_family(),
        is_linux=system == "linux",
        is_macos=system == "darwin",
        is_windows=system == "windows",
        is_wsl=_detect_wsl(),
    )


def is_root() -> bool:
    return os.getuid() == 0


def is_posix() -> bool:
    return os.name == "posix"
