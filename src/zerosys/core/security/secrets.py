from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from zerosys.utils.text import mask_secret

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "private_key",
        "privatekey",
        "ssh_key",
        "passphrase",
    }
)

_SENSITIVE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(key) for key in sorted(SENSITIVE_KEYS)) + r")=(\S+)",
    re.IGNORECASE,
)


@dataclass
class Secret:
    name: str
    value: str
    reveal: bool = False

    def __str__(self) -> str:
        if self.reveal:
            return self.value
        return mask_secret(self.value)

    def __repr__(self) -> str:
        return f"Secret(name={self.name!r}, value={str(self)!r})"


def is_sensitive_key(key: str) -> bool:
    return key.strip().lower() in SENSITIVE_KEYS


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        if is_sensitive_key(key):
            result[key] = mask_secret(str(value))
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, list):
            result[key] = _redact_list(value)
        else:
            result[key] = value
    return result


def _redact_list(items: list[Any]) -> list[Any]:
    result: list[Any] = []
    for item in items:
        if isinstance(item, dict):
            result.append(redact_dict(item))
        elif isinstance(item, list):
            result.append(_redact_list(item))
        else:
            result.append(item)
    return result


def redact_text(text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = match.group(2)
        return f"{key}={mask_secret(value)}"

    return _SENSITIVE_PATTERN.sub(_replace, text)


@dataclass
class SecretStore:
    _items: dict[str, Secret] = field(default_factory=dict)

    def set(self, name: str, value: str) -> None:
        self._items[name] = Secret(name=name, value=value)

    def get(self, name: str, reveal: bool = False) -> str | None:
        entry = self._items.get(name)
        if entry is None:
            return None
        return entry.value if reveal else str(entry)

    def has(self, name: str) -> bool:
        return name in self._items

    def remove(self, name: str) -> bool:
        return self._items.pop(name, None) is not None

    def clear(self) -> None:
        self._items.clear()

    def names(self) -> list[str]:
        return sorted(self._items.keys())

    def __len__(self) -> int:
        return len(self._items)
