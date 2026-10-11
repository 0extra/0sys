from __future__ import annotations

import pytest
from pydantic import ValidationError

from zerosys.core.config.schema import CONFIG_VERSION, Config, ProxyConfig

pytestmark = pytest.mark.unit


def test_proxy_config_defaults() -> None:
    proxy = ProxyConfig()

    assert proxy.enabled is False
    assert proxy.runtime == "docker"
    assert proxy.port == 8443
    assert proxy.sni == "www.microsoft.com"
    assert proxy.max_connections == 512
    assert proxy.log_level == "info"
    assert proxy.version == "0.1.5"
    assert proxy.install_dir == "/opt/0tpe"
    assert proxy.ssh_keys == []


def test_proxy_config_in_config() -> None:
    config = Config(
        version=CONFIG_VERSION,
        proxy=ProxyConfig(enabled=True, port=9443, sni="example.com"),
    )

    assert config.proxy is not None
    assert config.proxy.enabled is True
    assert config.proxy.port == 9443
    assert config.proxy.sni == "example.com"


def test_proxy_port_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        ProxyConfig(port=70000)


def test_proxy_log_level_validates() -> None:
    with pytest.raises(ValidationError):
        ProxyConfig(log_level="verbose")  # type: ignore[arg-type]


def test_proxy_deduplicates_ssh_keys() -> None:
    proxy = ProxyConfig(ssh_keys=["a", "b", "a"])

    assert proxy.ssh_keys == ["a", "b"]


def test_proxy_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        ProxyConfig(unknown="x")  # type: ignore[call-arg]
