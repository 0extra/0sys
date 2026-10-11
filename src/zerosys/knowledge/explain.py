from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from zerosys.core.errors import ZeroSysError

KNOWLEDGE_DIR = Path(__file__).resolve().parent
GLOSSARY_PATH = KNOWLEDGE_DIR / "glossary.yaml"
TIPS_PATH = KNOWLEDGE_DIR / "tips.yaml"


class KnowledgeError(ZeroSysError):
    pass


@dataclass(frozen=True)
class Term:
    key: str
    term: str
    simple: str
    why: str
    example: str

    def one_liner(self) -> str:
        return self.simple

    def full(self) -> str:
        parts = [f"{self.term}: {self.simple}"]
        if self.why:
            parts.append(f"Why it matters: {self.why}")
        if self.example:
            parts.append(f"Example: {self.example}")
        return "\n".join(parts)


class _KnowledgeHolder:
    def __init__(self) -> None:
        self.glossary: dict[str, Term] | None = None
        self.tips: dict[str, list[str]] | None = None

    def reset(self) -> None:
        self.glossary = None
        self.tips = None


_holder = _KnowledgeHolder()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise KnowledgeError(f"knowledge file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise KnowledgeError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise KnowledgeError(f"expected mapping in {path}")
    return data


def _load_glossary() -> dict[str, Term]:
    if _holder.glossary is not None:
        return _holder.glossary

    raw = _load_yaml(GLOSSARY_PATH)
    terms: dict[str, Term] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        terms[key] = Term(
            key=key,
            term=str(value.get("term", key)),
            simple=str(value.get("simple", "")),
            why=str(value.get("why", "")),
            example=str(value.get("example", "")),
        )
    _holder.glossary = terms
    return terms


def _load_tips() -> dict[str, list[str]]:
    if _holder.tips is not None:
        return _holder.tips

    raw = _load_yaml(TIPS_PATH)
    tips: dict[str, list[str]] = {}
    for key, value in raw.items():
        if isinstance(value, list):
            tips[key] = [str(item) for item in value]
    _holder.tips = tips
    return tips


def reset_cache() -> None:
    _holder.reset()


def lookup(key: str) -> Term | None:
    return _load_glossary().get(key)


def explain(key: str) -> str:
    term = lookup(key)
    if term is None:
        return f"No explanation available for '{key}'."
    return term.full()


def one_liner(key: str) -> str:
    term = lookup(key)
    if term is None:
        return ""
    return term.one_liner()


def all_terms() -> list[Term]:
    return sorted(_load_glossary().values(), key=lambda t: t.key)


def tips(category: str) -> list[str]:
    return list(_load_tips().get(category, []))


def all_categories() -> list[str]:
    return sorted(_load_tips().keys())
