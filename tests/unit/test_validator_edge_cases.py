from __future__ import annotations

import pytest
from pydantic import ValidationError

from zerosys.core.config.schema import (
    CONFIG_VERSION,
    CommandEntry,
    Config,
)
from zerosys.core.config.validator import validate

pytestmark = pytest.mark.unit


def test_pydantic_blocks_empty_command_name() -> None:
    with pytest.raises(ValidationError, match="at least 1 character"):
        CommandEntry(name="   ", run="echo hi")


def test_pydantic_blocks_empty_command_run() -> None:
    with pytest.raises(ValidationError, match="at least 1 character"):
        CommandEntry(name="deploy", run="   ")


def test_duplicate_command_name() -> None:
    config = Config(
        version=CONFIG_VERSION,
        commands=[
            CommandEntry(name="deploy", run="echo 1"),
            CommandEntry(name="deploy", run="echo 2"),
        ],
    )
    report = validate(config)

    warnings = {i.code for i in report.warnings()}
    assert "CMD001" in warnings
