from __future__ import annotations

import pytest

from zerosys.core.security.secrets import (
    Secret,
    SecretStore,
    is_sensitive_key,
    redact_dict,
    redact_text,
)

pytestmark = pytest.mark.unit


def test_secret_str_masks_value() -> None:
    secret = Secret(name="db_password", value="supersecretvalue")

    rendered = str(secret)

    assert "supersecretvalue" not in rendered
    assert rendered.startswith("supe")


def test_secret_str_reveals_when_flagged() -> None:
    secret = Secret(name="x", value="visible", reveal=True)

    assert str(secret) == "visible"


def test_secret_repr_masks() -> None:
    secret = Secret(name="token", value="abcdefgh")

    assert "abcdefgh" not in repr(secret)
    assert "Secret" in repr(secret)


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


def test_redact_dict_recurses_into_nested_lists() -> None:
    data = {"outer": [["secret123"]]}

    result = redact_dict(data)

    assert "secret123" in str(result)


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
    assert "password=" in result
    assert "token=" in result


def test_redact_text_multiple_lines() -> None:
    text = "first password=aaaa\nsecond token=bbbb\nthird ok"

    result = redact_text(text)

    assert "aaaa" not in result
    assert "bbbb" not in result
    assert "third ok" in result


def test_redact_text_case_insensitive() -> None:
    text = "PASSWORD=topsecret"

    result = redact_text(text)

    assert "topsecret" not in result


def test_redact_text_word_boundary() -> None:
    text = "notapassword=keepme"

    result = redact_text(text)

    assert "keepme" in result


def test_secret_store_set_and_get() -> None:
    store = SecretStore()
    store.set("db", "value123")

    assert store.get("db", reveal=True) == "value123"
    assert "value123" not in (store.get("db") or "")


def test_secret_store_has_and_remove() -> None:
    store = SecretStore()
    store.set("k", "v")

    assert store.has("k") is True
    assert store.remove("k") is True
    assert store.has("k") is False


def test_secret_store_names_sorted() -> None:
    store = SecretStore()
    store.set("z", "1")
    store.set("a", "2")

    assert store.names() == ["a", "z"]


def test_secret_store_clear() -> None:
    store = SecretStore()
    store.set("x", "1")
    store.set("y", "2")
    store.clear()

    assert len(store) == 0


def test_secret_store_get_unknown_returns_none() -> None:
    store = SecretStore()

    assert store.get("missing") is None
