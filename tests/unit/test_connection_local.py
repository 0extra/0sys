from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.connection.local import ConnectionError, LocalConnection

pytestmark = pytest.mark.unit


@pytest.fixture
def conn() -> LocalConnection:
    return LocalConnection()


def test_run_returns_result(conn: LocalConnection) -> None:
    result = conn.run("echo hi")

    assert result.success
    assert "hi" in result.stdout


def test_run_failing(conn: LocalConnection) -> None:
    result = conn.run("exit 5")

    assert result.success is False
    assert result.exit_code == 5


def test_run_check_raises(conn: LocalConnection) -> None:
    with pytest.raises(ConnectionError):
        conn.run("exit 1", check=True)


def test_run_argv(conn: LocalConnection) -> None:
    result = conn.run_argv(["echo", "hello world"])

    assert result.success
    assert "hello world" in result.stdout


def test_exists_true(conn: LocalConnection, tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    path.write_text("x", encoding="utf-8")

    assert conn.exists(str(path)) is True


def test_exists_false(conn: LocalConnection, tmp_path: Path) -> None:
    assert conn.exists(str(tmp_path / "missing")) is False


def test_read_file(conn: LocalConnection, tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    path.write_text("hello", encoding="utf-8")

    assert conn.read_file(str(path)) == "hello"


def test_write_file(conn: LocalConnection, tmp_path: Path) -> None:
    path = tmp_path / "out.txt"
    conn.write_file(str(path), "content")

    assert path.read_text(encoding="utf-8") == "content"


def test_close_is_noop(conn: LocalConnection) -> None:
    conn.close()
