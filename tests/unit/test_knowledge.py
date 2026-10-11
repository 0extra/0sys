from __future__ import annotations

import pytest

from zerosys.knowledge import (
    Term,
    all_categories,
    all_terms,
    explain,
    lookup,
    one_liner,
    reset_cache,
    tips,
)

pytestmark = pytest.mark.unit


def test_lookup_known_term() -> None:
    reset_cache()
    entry = lookup("ufw")

    assert entry is not None
    assert isinstance(entry, Term)
    assert entry.key == "ufw"


def test_lookup_unknown_returns_none() -> None:
    reset_cache()
    assert lookup("nonsense-term-xyz") is None


def test_explain_returns_multiline() -> None:
    reset_cache()
    text = explain("firewall")

    assert "Firewall" in text
    assert "Why it matters" in text


def test_explain_unknown_term_message() -> None:
    reset_cache()
    result = explain("nonsense-term-xyz")

    assert "No explanation" in result


def test_one_liner_for_known_term() -> None:
    reset_cache()
    result = one_liner("ssh")

    assert result
    assert "log in" in result.lower() or "safe" in result.lower()


def test_one_liner_unknown_is_empty() -> None:
    reset_cache()
    assert one_liner("nonsense-term-xyz") == ""


def test_all_terms_sorted() -> None:
    reset_cache()
    terms = all_terms()

    keys = [t.key for t in terms]
    assert keys == sorted(keys)
    assert len(terms) >= 8


def test_tips_known_category() -> None:
    reset_cache()
    result = tips("firewall")

    assert isinstance(result, list)
    assert len(result) >= 1


def test_tips_unknown_category_is_empty() -> None:
    reset_cache()
    assert tips("nonsense-category-xyz") == []


def test_all_categories_non_empty() -> None:
    reset_cache()
    categories = all_categories()

    assert "firewall" in categories
    assert "ssh" in categories


def test_reset_cache_forces_reload() -> None:
    reset_cache()
    first = lookup("ufw")
    reset_cache()
    second = lookup("ufw")

    assert first is not None
    assert second is not None
    assert first.key == second.key
