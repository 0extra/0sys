from __future__ import annotations

import re
from typing import Any

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
        "passphrase",
    }
)

_SECRETS_REGEX = re.compile(
    r"(?i)(\b(?:password|passwd|secret|token|api_key|apikey|access_key|private_key|privatekey|passphrase)\b\s*[:=]\s*[\"']?)([^\"'\s]+)([\"']?)"
)


def mask_secret(value: str, visible: int = 4) -> str:
    if len(value) <= visible:
        return "*" * len(value)
    return value[:visible] + "*" * (len(value) - visible)


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_")


def is_sensitive_key(key: str) -> bool:
    return _normalize_key(key) in SENSITIVE_KEYS


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
        prefix = match.group(1)
        value = match.group(2)
        suffix = match.group(3)
        return f"{prefix}{mask_secret(value)}{suffix}"

    return _SECRETS_REGEX.sub(_replace, text)
