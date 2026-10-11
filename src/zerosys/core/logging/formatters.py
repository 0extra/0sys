from __future__ import annotations

import logging

from zerosys.core.security.secrets import redact_text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        return redact_text(rendered)


def build_redacting_formatter(
    fmt: str,
    datefmt: str | None = None,
) -> RedactingFormatter:
    return RedactingFormatter(fmt, datefmt=datefmt)
