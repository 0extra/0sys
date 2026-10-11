from __future__ import annotations

from zerosys.cli.commands import (
    apply,
    check,
    doctor,
    examples,
    explain,
    explain_term,
    init,
    plan,
    rollback,
    tips,
)
from zerosys.cli.commands.cloud_init import cloud_init_command

__all__ = [
    "apply",
    "check",
    "cloud_init_command",
    "doctor",
    "examples",
    "explain",
    "explain_term",
    "init",
    "plan",
    "rollback",
    "tips",
]
