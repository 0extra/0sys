from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from zerosys.core.errors import ZeroSysError


class FileSystemError(ZeroSysError):
    pass


def ensure_dir(path: Path | str) -> Path:
    target = Path(path).expanduser().resolve()
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise FileSystemError(f"cannot create directory {target}: {exc}") from exc
    return target


def read_text(path: Path | str, encoding: str = "utf-8") -> str:
    target = Path(path).expanduser().resolve()
    try:
        return target.read_text(encoding=encoding)
    except OSError as exc:
        raise FileSystemError(f"cannot read {target}: {exc}") from exc


def write_text(
    path: Path | str,
    content: str,
    encoding: str = "utf-8",
    create_parents: bool = True,
) -> Path:
    target = Path(path).expanduser().resolve()
    if create_parents:
        ensure_dir(target.parent)
    try:
        target.write_text(content, encoding=encoding)
    except OSError as exc:
        raise FileSystemError(f"cannot write {target}: {exc}") from exc
    return target


def copy_file(source: Path | str, destination: Path | str) -> Path:
    src = Path(source).expanduser().resolve()
    dst = Path(destination).expanduser().resolve()
    if not src.exists():
        raise FileSystemError(f"source not found: {src}")
    ensure_dir(dst.parent)
    try:
        shutil.copy2(src, dst)
    except OSError as exc:
        raise FileSystemError(f"cannot copy {src} to {dst}: {exc}") from exc
    return dst


def file_exists(path: Path | str) -> bool:
    return Path(path).expanduser().exists()


def delete_file(path: Path | str, missing_ok: bool = True) -> bool:
    target = Path(path).expanduser()
    if not target.exists():
        if missing_ok:
            return False
        raise FileSystemError(f"file not found: {target}")
    try:
        target.unlink()
    except OSError as exc:
        raise FileSystemError(f"cannot delete {target}: {exc}") from exc
    return True


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def expand_path(path: str) -> Path:
    return Path(os.path.expandvars(path)).expanduser().resolve()


@contextmanager
def temporary_dir(prefix: str = "0sys-") -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
        yield Path(tmp)


@contextmanager
def temporary_file(
    prefix: str = "0sys-",
    suffix: str = "",
    content: str | None = None,
) -> Iterator[Path]:
    fd, raw_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    path = Path(raw_path)
    try:
        if content is not None:
            os.write(fd, content.encode("utf-8"))
        os.close(fd)
        yield path
    finally:
        if path.exists():
            path.unlink()
