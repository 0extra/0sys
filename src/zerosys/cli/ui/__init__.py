from __future__ import annotations

from zerosys.cli.commands.proxy import (
    proxy_client_config_command,
    proxy_fetch_certs_command,
    proxy_server_info_command,
    proxy_show_config_command,
)
from zerosys.cli.ui.banner import print_banner, print_mini_banner, render_logo
from zerosys.cli.ui.explainer import (
    explain_task,
    kind_label,
    print_error,
    print_hint,
    print_success,
    print_task_error,
    print_task_finish,
    print_task_start,
    print_warning,
)
from zerosys.cli.ui.progress import NullReporter, ProgressReporter
from zerosys.cli.ui.prompts import (
    ask_choice,
    ask_confirm,
    ask_int,
    ask_multi_choice,
    ask_text,
)
from zerosys.cli.ui.theme import (
    PALETTE,
    RICH_THEME,
    build_console,
    get_console,
    set_console,
)

__all__ = [
    "PALETTE",
    "RICH_THEME",
    "NullReporter",
    "ProgressReporter",
    "apply",
    "ask_choice",
    "ask_confirm",
    "ask_int",
    "ask_multi_choice",
    "ask_text",
    "build_console",
    "check",
    "cloud_init_command",
    "doctor",
    "examples",
    "explain",
    "explain_task",
    "explain_term",
    "get_console",
    "init",
    "kind_label",
    "nixos_command",
    "plan",
    "print_banner",
    "print_error",
    "print_hint",
    "print_mini_banner",
    "print_success",
    "print_task_error",
    "print_task_finish",
    "print_task_start",
    "print_warning",
    "proxy_client_config_command",
    "proxy_fetch_certs_command",
    "proxy_server_info_command",
    "proxy_show_config_command",
    "render_logo",
    "rollback_command",
    "set_console",
    "terraform_command",
    "tips",
]
