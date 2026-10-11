from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.backends.base import BackendContext
from zerosys.backends.terraform import (
    TERRAFORM_HEADER,
    TerraformBackend,
    TerraformError,
    TerraformGenerator,
    generate_terraform,
)
from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    InfrastructureConfig,
    ServerConfig,
)
from zerosys.core.planner.task import Task, TaskKind, TaskStatus

pytestmark = pytest.mark.unit


@pytest.fixture
def generator() -> TerraformGenerator:
    return TerraformGenerator()


@pytest.fixture
def hetzner_config() -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="web-01"),
        infrastructure=InfrastructureConfig(
            provider="hetzner",
            region="nbg1",
            server_type="cx22",
            image="ubuntu-24.04",
            ssh_keys=["my-key"],
            tags=["env:prod"],
        ),
    )


@pytest.fixture
def digitalocean_config() -> Config:
    return Config(
        version=CONFIG_VERSION,
        infrastructure=InfrastructureConfig(
            provider="digitalocean",
            region="fra1",
            server_type="s-1vcpu-1gb",
            image="ubuntu-24-04-x64",
        ),
    )


def test_generate_requires_infrastructure(generator: TerraformGenerator) -> None:
    config = Config(version=CONFIG_VERSION)

    with pytest.raises(TerraformError, match="infrastructure"):
        generator.generate(config)


def test_generate_returns_three_files(
    generator: TerraformGenerator, hetzner_config: Config
) -> None:
    files = generator.generate(hetzner_config)

    assert set(files.keys()) == {"main.tf", "variables.tf", "outputs.tf"}


def test_all_files_start_with_header(generator: TerraformGenerator, hetzner_config: Config) -> None:
    files = generator.generate(hetzner_config)

    for content in files.values():
        assert content.startswith(TERRAFORM_HEADER)


def test_hetzner_main_contains_provider(
    generator: TerraformGenerator, hetzner_config: Config
) -> None:
    main = generator.generate(hetzner_config)["main.tf"]

    assert "hetznercloud/hcloud" in main
    assert 'resource "hcloud_server" "main"' in main


def test_hetzner_main_uses_server_settings(
    generator: TerraformGenerator, hetzner_config: Config
) -> None:
    main = generator.generate(hetzner_config)["main.tf"]

    assert 'name        = "web-01"' in main
    assert 'server_type = "cx22"' in main
    assert 'image       = "ubuntu-24.04"' in main
    assert 'location    = "nbg1"' in main
    assert 'ssh_keys    = ["my-key"]' in main


def test_hetzner_main_includes_tags(generator: TerraformGenerator, hetzner_config: Config) -> None:
    main = generator.generate(hetzner_config)["main.tf"]

    assert 'env = "prod"' in main
    assert 'managed_by = "0sys"' in main


def test_digitalocean_main(generator: TerraformGenerator, digitalocean_config: Config) -> None:
    main = generator.generate(digitalocean_config)["main.tf"]

    assert "digitalocean/digitalocean" in main
    assert 'resource "digitalocean_droplet" "main"' in main
    assert 'size   = "s-1vcpu-1gb"' in main
    assert 'region = "fra1"' in main
    assert '"managed_by:0sys"' in main


def test_outputs_hetzner(generator: TerraformGenerator, hetzner_config: Config) -> None:
    outputs = generator.generate(hetzner_config)["outputs.tf"]

    assert "hcloud_server.main.ipv4_address" in outputs
    assert "hcloud_server.main.id" in outputs


def test_outputs_digitalocean(generator: TerraformGenerator, digitalocean_config: Config) -> None:
    outputs = generator.generate(digitalocean_config)["outputs.tf"]

    assert "digitalocean_droplet.main.ipv4_address" in outputs
    assert "digitalocean_droplet.main.id" in outputs


def test_variables_tf_has_token(generator: TerraformGenerator, hetzner_config: Config) -> None:
    variables = generator.generate(hetzner_config)["variables.tf"]

    assert 'variable "provider_token"' in variables
    assert "sensitive   = true" in variables


def test_name_falls_back_to_hostname(generator: TerraformGenerator, hetzner_config: Config) -> None:
    main = generator.generate(hetzner_config)["main.tf"]

    assert 'name        = "web-01"' in main


def test_explicit_name_overrides_hostname(generator: TerraformGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="web-01"),
        infrastructure=InfrastructureConfig(
            provider="hetzner",
            region="nbg1",
            server_type="cx22",
            name="custom-name",
        ),
    )

    main = generator.generate(config)["main.tf"]

    assert 'name        = "custom-name"' in main


def test_backend_write_creates_files(tmp_path: Path, hetzner_config: Config) -> None:
    backend = TerraformBackend()
    target = tmp_path / "tf"

    written = backend.write(hetzner_config, target)

    assert len(written) == 3
    assert all(p.exists() for p in written)
    assert (target / "main.tf").exists()


def test_backend_supports_returns_false(hetzner_config: Config) -> None:
    backend = TerraformBackend()
    task = Task(kind=TaskKind.SERVER, name="x")

    assert backend.supports(task) is False


def test_backend_validate_missing_infrastructure() -> None:
    backend = TerraformBackend()
    config = Config(version=CONFIG_VERSION)

    issues = backend.validate(config)

    assert issues
    assert "infrastructure" in issues[0]


def test_backend_validate_ok(hetzner_config: Config) -> None:
    backend = TerraformBackend()

    issues = backend.validate(hetzner_config)

    assert issues == []


def test_generate_terraform_function(hetzner_config: Config) -> None:
    files = generate_terraform(hetzner_config)

    assert "main.tf" in files


def test_backend_name() -> None:
    assert TerraformBackend().name == "terraform"


def test_backend_run_returns_skipped(hetzner_config: Config) -> None:
    backend = TerraformBackend()
    task = Task(kind=TaskKind.SERVER, name="x")
    result = backend.run(task, BackendContext(target_host="localhost"))

    assert result.status is TaskStatus.SKIPPED
