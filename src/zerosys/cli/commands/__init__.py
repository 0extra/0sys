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
from zerosys.cli.commands.nixos import nixos_command
from zerosys.cli.commands.terraform import terraform_command

__all__ = [
    "apply",
    "check",
    "cloud_init_command",
    "doctor",
    "examples",
    "explain",
    "explain_term",
    "init",
    "nixos_command",
    "plan",
    "rollback",
    "terraform_command",
    "tips",
]
