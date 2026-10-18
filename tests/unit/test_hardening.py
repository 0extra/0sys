from __future__ import annotations

import pytest

from zerosys.core.config.schema import CONFIG_VERSION, Config, FirewallConfig
from zerosys.core.config.validator import validate
from zerosys.core.security.secrets import redact_dict, redact_text

pytestmark = pytest.mark.unit


def test_fw005_blocks_custom_connection_port() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22]),
    )
    report = validate(config, connect_port=2222)
    codes = {i.code for i in report.issues}
    assert "FW005" in codes


def test_fw005_allows_correct_port() -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[2222]),
    )
    report = validate(config, connect_port=2222)
    codes = {i.code for i in report.issues}
    assert "FW005" not in codes


def test_redact_text_multiple_secrets() -> None:
    text = "connecting to db with password=supersecret and token=12345"
    result = redact_text(text)
    assert "supersecret" not in result
    assert "12345" not in result
    assert "password=" in result


def test_redact_dict_nested_list() -> None:
    data = {"users": [{"name": "admin", "password": "secret1"}]}
    result = redact_dict(data)
    assert "secret1" not in str(result)
    assert result["users"][0]["name"] == "admin"
