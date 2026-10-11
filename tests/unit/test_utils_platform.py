from __future__ import annotations

import pytest

from zerosys.utils.platform import (
    OSFamily,
    detect_platform,
    is_posix,
    is_root,
)

pytestmark = pytest.mark.unit


def test_detect_platform_returns_dataclass() -> None:
    info = detect_platform()

    assert info.system in {"linux", "darwin", "windows"}
    assert info.machine
    assert info.release
    assert isinstance(info.family, OSFamily)


def test_detect_platform_on_linux() -> None:
    info = detect_platform()

    if info.system == "linux":
        assert info.is_linux is True
        assert info.is_macos is False
        assert info.is_windows is False


def test_is_posix_on_linux() -> None:
    assert is_posix() is True


def test_is_root_returns_bool() -> None:
    assert isinstance(is_root(), bool)


def test_os_family_values_are_strings() -> None:
    for member in OSFamily:
        assert isinstance(member.value, str)
