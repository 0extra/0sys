from __future__ import annotations

import pytest

from zerosys.utils.text import (
    dedent,
    format_duration,
    indent,
    is_valid_env_key,
    mask_secret,
    pluralize,
    slugify,
    split_lines,
    strip_ansi,
    truncate,
)

pytestmark = pytest.mark.unit


def test_strip_ansi_removes_escape_sequences() -> None:
    assert strip_ansi("\x1b[31mred\x1b[0m") == "red"


def test_strip_ansi_leaves_plain_text() -> None:
    assert strip_ansi("hello") == "hello"


def test_slugify_lowercases_and_replaces() -> None:
    assert slugify("Hello World!") == "hello-world"


def test_slugify_collapses_separators() -> None:
    assert slugify("a   ---   b") == "a-b"


def test_slugify_empty_returns_placeholder() -> None:
    assert slugify("!!!") == "unnamed"


def test_truncate_short_string_unchanged() -> None:
    assert truncate("hello", length=10) == "hello"


def test_truncate_long_string_cuts() -> None:
    result = truncate("a" * 100, length=10)
    assert len(result) == 10
    assert result.endswith("...")


def test_truncate_very_small_length() -> None:
    assert truncate("abcdef", length=3) == "abc"


def test_indent_prefixes_every_line() -> None:
    result = indent("a\nb", prefix="-- ")
    assert result == "-- a\n-- b"


def test_indent_leaves_empty_lines() -> None:
    result = indent("a\n\nb", prefix="> ")
    assert result == "> a\n\n> b"


def test_dedent_removes_common_indent() -> None:
    text = "    a\n    b\n    c"
    assert dedent(text) == "a\nb\nc"


def test_is_valid_env_key_accepts_uppercase() -> None:
    assert is_valid_env_key("MY_VAR") is True


def test_is_valid_env_key_rejects_digits_first() -> None:
    assert is_valid_env_key("1VAR") is False


def test_pluralize_singular() -> None:
    assert pluralize(1, "package") == "package"


def test_pluralize_plural_default() -> None:
    assert pluralize(3, "package") == "packages"


def test_pluralize_custom_plural() -> None:
    assert pluralize(2, "box", "boxes") == "boxes"


def test_format_duration_ms() -> None:
    assert format_duration(0.5) == "500 ms"


def test_format_duration_seconds() -> None:
    assert format_duration(5.0) == "5.0 s"


def test_format_duration_minutes() -> None:
    assert format_duration(125.0) == "2 min 5 s"


def test_format_duration_hours() -> None:
    assert format_duration(7200.0).startswith("2 h")


def test_mask_secret_short_value() -> None:
    assert mask_secret("abc", visible=4) == "***"


def test_mask_secret_long_value() -> None:
    result = mask_secret("supersecret", visible=4)
    assert result.startswith("supe")
    assert set(result[4:]) == {"*"}


def test_split_lines_drops_empty() -> None:
    assert split_lines("a\n\n b \n") == ["a", " b "]
