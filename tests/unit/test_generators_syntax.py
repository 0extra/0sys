from __future__ import annotations

import pytest
import yaml

from zerosys.backends.cloudinit import CloudInitGenerator
from zerosys.backends.nixos import NixosGenerator
from zerosys.backends.terraform import TerraformGenerator
from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FirewallConfig,
    InfrastructureConfig,
    PackagesConfig,
    ServerConfig,
)

pytestmark = pytest.mark.unit


def _sample_config() -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="test", timezone="UTC"),
        packages=PackagesConfig(install=["nginx"]),
        firewall=FirewallConfig(default="deny", allow=[22, 80]),
        infrastructure=InfrastructureConfig(
            provider="hetzner",
            region="nbg1",
            server_type="cx22",
        ),
    )


def test_cloudinit_generates_valid_yaml() -> None:
    config = _sample_config()
    generator = CloudInitGenerator()
    content = generator.generate(config)

    assert content.startswith("#cloud-config\n")
    data = yaml.safe_load(content.replace("#cloud-config\n", "", 1))
    assert isinstance(data, dict)
    assert data["hostname"] == "test"
    assert "nginx" in data["packages"]


def test_nixos_generates_balanced_brackets() -> None:
    config = _sample_config()
    generator = NixosGenerator()
    content = generator.generate(config)

    assert content.count("{") == content.count("}")
    assert content.count("[") == content.count("]")
    assert 'networking.hostName = "test";' in content


def test_terraform_generates_expected_files() -> None:
    config = _sample_config()
    generator = TerraformGenerator()
    files = generator.generate(config)

    assert "main.tf" in files
    assert "variables.tf" in files
    assert "outputs.tf" in files
    assert 'resource "hcloud_server" "main"' in files["main.tf"]
