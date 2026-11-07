from __future__ import annotations

import pytest

from zerosys.core.security.secrets import (
    is_sensitive_key,
    mask_secret,
    redact_dict,
    redact_text,
)

pytestmark = pytest.mark.unit


def test_mask_secret_short_value() -> None:
    assert mask_secret("abc", visible=4) == "***"


def test_mask_secret_long_value() -> None:
    result = mask_secret("supersecret", visible=4)
    assert result.startswith("supe")
    assert set(result[4:]) == {"*"}


def test_is_sensitive_key_recognizes_tokens() -> None:
    assert is_sensitive_key("password") is True
    assert is_sensitive_key("API_KEY") is True
    assert is_sensitive_key("token") is True


def test_is_sensitive_key_ignores_normal_keys() -> None:
    assert is_sensitive_key("hostname") is False
    assert is_sensitive_key("port") is False


def test_redact_dict_masks_sensitive_values() -> None:
    data = {"hostname": "web-01", "password": "supersecret"}
    result = redact_dict(data)
    assert result["hostname"] == "web-01"
    assert "supersecret" not in str(result["password"])


def test_redact_dict_recurses() -> None:
    data = {"outer": {"token": "abcdefghij"}}
    result = redact_dict(data)
    assert isinstance(result["outer"], dict)
    assert "abcdefghij" not in str(result["outer"]["token"])  # type: ignore[index]


def test_redact_dict_recurses_into_lists() -> None:
    data = {"items": [{"password": "aaaa"}, {"password": "bbbb"}]}
    result = redact_dict(data)
    assert isinstance(result["items"], list)
    assert "aaaa" not in str(result["items"])
    assert "bbbb" not in str(result["items"])


def test_redact_dict_keeps_safe_values_in_lists() -> None:
    data = {"items": [{"host": "web-01"}, {"host": "web-02"}]}
    result = redact_dict(data)
    assert result["items"][0]["host"] == "web-01"  # type: ignore[index]
    assert result["items"][1]["host"] == "web-02"  # type: ignore[index]


def test_redact_text_masks_after_marker() -> None:
    text = "connecting with password=supersecret123"
    result = redact_text(text)
    assert "supersecret123" not in result
    assert "password=" in result


def test_redact_text_leaves_clean_string() -> None:
    text = "all good here"
    assert redact_text(text) == text


def test_redact_text_masks_multiple_markers() -> None:
    text = "password=aaaa token=bbbb"
    result = redact_text(text)
    assert "aaaa" not in result
    assert "bbbb" not in result


def test_redact_text_case_insensitive() -> None:
    text = "PASSWORD=topsecret"
    result = redact_text(text)
    assert "topsecret" not in result


def test_redact_text_word_boundary() -> None:
    text = "notapassword=keepme"
    result = redact_text(text)
    assert "keepme" in result
