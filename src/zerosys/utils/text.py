from __future__ import annotations

import re

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
VALID_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    replaced = re.sub(r"[^a-z0-9]+", "-", lowered)
    return replaced.strip("-") or "unnamed"


def truncate(text: str, length: int = 80, ellipsis: str = "...") -> str:
    if len(text) <= length:
        return text
    if length <= len(ellipsis):
        return text[:length]
    return text[: length - len(ellipsis)] + ellipsis


def indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def dedent(text: str) -> str:
    lines = text.splitlines()
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return text
    common = min(len(line) - len(line.lstrip()) for line in non_empty)
    return "\n".join(line[common:] if line else line for line in lines)


def is_valid_env_key(key: str) -> bool:
    return bool(VALID_ENV_KEY.match(key))


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return singular
    return plural if plural is not None else f"{singular}s"


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{int(seconds * 1000)} ms"
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes} min {secs} s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"


def mask_secret(value: str, visible: int = 4) -> str:
    if len(value) <= visible:
        return "*" * len(value)
    return value[:visible] + "*" * (len(value) - visible)


def split_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]
