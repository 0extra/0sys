from __future__ import annotations

from zerosys.cli.commands import (
    doctor,
    examples,
    explain,
    explain_term,
    init,
    tips,
)
from zerosys.cli.commands.apply import apply_command
from zerosys.cli.commands.check import check_command
from zerosys.cli.commands.cloud_init import cloud_init_command
from zerosys.cli.commands.nixos import nixos_command
from zerosys.cli.commands.plan import plan_command
from zerosys.cli.commands.proxy import (
    proxy_client_config_command,
    proxy_fetch_certs_command,
    proxy_server_info_command,
    proxy_show_config_command,
)
from zerosys.cli.commands.rollback import rollback_command
from zerosys.cli.commands.terraform import terraform_command

__all__ = [
    "apply_command",
    "check_command",
    "cloud_init_command",
    "doctor",
    "examples",
    "explain",
    "explain_term",
    "init",
    "nixos_command",
    "plan_command",
    "proxy_client_config_command",
    "proxy_fetch_certs_command",
    "proxy_server_info_command",
    "proxy_show_config_command",
    "rollback_command",
    "terraform_command",
    "tips",
]
