from __future__ import annotations

import pytest

from zerosys.utils.shell import (
    CommandResult,
    ShellError,
    has_command,
    quote,
    run,
    which,
)

pytestmark = pytest.mark.unit


def test_run_simple_string_command() -> None:
    result = run("echo hello")

    assert isinstance(result, CommandResult)
    assert result.success
    assert "hello" in result.stdout


def test_run_list_command() -> None:
    result = run(["echo", "hello"])

    assert result.success
    assert "hello" in result.stdout


def test_run_failing_command() -> None:
    result = run("exit 3")

    assert result.success is False
    assert result.exit_code == 3


def test_run_check_raises() -> None:
    with pytest.raises(ShellError, match="command failed"):
        run("exit 1", check=True)


def test_run_timeout_raises() -> None:
    with pytest.raises(ShellError, match="timed out"):
        run("sleep 5", timeout=1)


def test_command_result_str() -> None:
    result = run("echo ok")

    assert "echo ok" in str(result)


def test_which_finds_sh() -> None:
    assert which("sh") is not None


def test_which_returns_none_for_missing() -> None:
    assert which("definitely-not-a-real-binary-xyz") is None


def test_has_command_true_for_sh() -> None:
    assert has_command("sh") is True


def test_quote_escapes_spaces() -> None:
    result = quote(["echo", "hello world"])

    assert "'hello world'" in result
