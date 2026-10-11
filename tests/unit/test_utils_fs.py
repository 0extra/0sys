from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.utils.fs import (
    FileSystemError,
    copy_file,
    delete_file,
    ensure_dir,
    expand_path,
    file_exists,
    human_size,
    read_text,
    temporary_dir,
    temporary_file,
    write_text,
)

pytestmark = pytest.mark.unit


def test_ensure_dir_creates_nested(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "c"
    result = ensure_dir(target)

    assert result.exists()
    assert result == target.resolve()


def test_ensure_dir_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "x"
    ensure_dir(target)
    ensure_dir(target)

    assert target.exists()


def test_write_and_read_text(tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    write_text(path, "hello")

    assert read_text(path) == "hello"


def test_write_text_creates_parents(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "nested" / "file.txt"
    write_text(path, "content")

    assert path.exists()


def test_read_text_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileSystemError):
        read_text(tmp_path / "missing.txt")


def test_copy_file(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_text("data", encoding="utf-8")
    dst = tmp_path / "nested" / "dst.txt"

    result = copy_file(src, dst)

    assert result.read_text(encoding="utf-8") == "data"


def test_copy_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileSystemError, match="source not found"):
        copy_file(tmp_path / "nope", tmp_path / "dst")


def test_file_exists(tmp_path: Path) -> None:
    path = tmp_path / "x.txt"
    assert file_exists(path) is False

    path.write_text("x", encoding="utf-8")
    assert file_exists(path) is True


def test_delete_file_existing(tmp_path: Path) -> None:
    path = tmp_path / "x.txt"
    path.write_text("x", encoding="utf-8")

    assert delete_file(path) is True
    assert not path.exists()


def test_delete_file_missing_ok(tmp_path: Path) -> None:
    assert delete_file(tmp_path / "missing.txt") is False


def test_delete_file_missing_strict(tmp_path: Path) -> None:
    with pytest.raises(FileSystemError):
        delete_file(tmp_path / "missing.txt", missing_ok=False)


@pytest.mark.parametrize(
    ("num_bytes", "expected_suffix"),
    [
        (100, "B"),
        (2048, "KB"),
        (1024 * 1024 * 3, "MB"),
    ],
)
def test_human_size(num_bytes: int, expected_suffix: str) -> None:
    assert human_size(num_bytes).endswith(expected_suffix)


def test_expand_path_handles_tilde() -> None:
    expanded = expand_path("~/some/file")

    assert expanded.is_absolute()
    assert "~" not in str(expanded)


def test_temporary_dir_lifecycle() -> None:
    with temporary_dir() as path:
        assert path.exists()
    assert not path.exists()


def test_temporary_file_with_content() -> None:
    with temporary_file(content="hello") as path:
        assert path.read_text(encoding="utf-8") == "hello"
    assert not path.exists()
