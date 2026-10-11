from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.core.errors import SecurityError
from zerosys.core.security.permissions import (
    PRIVATE_MODE,
    check_mode,
    ensure_secure_file,
    is_group_writable,
    is_insecure,
    is_owned_by_current_user,
    is_world_readable,
    is_world_writable,
    read_mode,
    set_mode,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    path = tmp_path / "file.txt"
    path.write_text("content", encoding="utf-8")
    return path


def test_read_mode_returns_octal(sample_file: Path) -> None:
    mode = read_mode(sample_file)

    assert isinstance(mode, int)
    assert 0 <= mode <= 0o777


def test_read_mode_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        read_mode(tmp_path / "missing.txt")


def test_set_mode_changes_permissions(sample_file: Path) -> None:
    set_mode(sample_file, PRIVATE_MODE)

    assert read_mode(sample_file) == PRIVATE_MODE


def test_set_mode_rejects_invalid(sample_file: Path) -> None:
    with pytest.raises(SecurityError):
        set_mode(sample_file, 0o1000)


def test_check_mode_ok(sample_file: Path) -> None:
    set_mode(sample_file, PRIVATE_MODE)

    result = check_mode(sample_file, PRIVATE_MODE)

    assert result.ok is True
    assert result.actual == PRIVATE_MODE


def test_check_mode_mismatch(sample_file: Path) -> None:
    set_mode(sample_file, 0o644)

    result = check_mode(sample_file, PRIVATE_MODE)

    assert result.ok is False
    assert result.expected == PRIVATE_MODE


def test_permission_check_describe(sample_file: Path) -> None:
    result = check_mode(sample_file, 0o644)
    description = result.describe()

    assert "expected" in description
    assert "got" in description


def test_is_world_readable(sample_file: Path) -> None:
    set_mode(sample_file, 0o644)
    assert is_world_readable(sample_file) is True

    set_mode(sample_file, 0o600)
    assert is_world_readable(sample_file) is False


def test_is_world_writable(sample_file: Path) -> None:
    set_mode(sample_file, 0o606)
    assert is_world_writable(sample_file) is True

    set_mode(sample_file, 0o600)
    assert is_world_writable(sample_file) is False


def test_is_group_writable(sample_file: Path) -> None:
    set_mode(sample_file, 0o660)
    assert is_group_writable(sample_file) is True

    set_mode(sample_file, 0o600)
    assert is_group_writable(sample_file) is False


def test_is_owned_by_current_user(sample_file: Path) -> None:
    assert is_owned_by_current_user(sample_file) is True


def test_ensure_secure_file_tightens(sample_file: Path) -> None:
    set_mode(sample_file, 0o644)

    ensure_secure_file(sample_file, mode=PRIVATE_MODE)

    assert read_mode(sample_file) == PRIVATE_MODE


def test_ensure_secure_file_noop_when_already_secure(sample_file: Path) -> None:
    set_mode(sample_file, PRIVATE_MODE)

    ensure_secure_file(sample_file, mode=PRIVATE_MODE)

    assert read_mode(sample_file) == PRIVATE_MODE


def test_is_insecure_detects_world_writable(sample_file: Path) -> None:
    set_mode(sample_file, 0o606)

    assert is_insecure(sample_file) is True


def test_is_insecure_returns_false_for_private(sample_file: Path) -> None:
    set_mode(sample_file, 0o600)

    assert is_insecure(sample_file) is False
