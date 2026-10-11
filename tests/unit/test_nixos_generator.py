from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.backends.base import BackendContext
from zerosys.backends.nixos import (
    NIX_HEADER,
    NixosBackend,
    NixosGenerator,
    generate_nixos,
)
from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FileEntry,
    FirewallConfig,
    PackagesConfig,
    ServerConfig,
    ServiceConfig,
    UserConfig,
)
from zerosys.core.planner.task import Task, TaskKind, TaskStatus

pytestmark = pytest.mark.unit


@pytest.fixture
def generator() -> NixosGenerator:
    return NixosGenerator()


def test_generate_starts_with_header(generator: NixosGenerator) -> None:
    config = Config(version=CONFIG_VERSION)

    content = generator.generate(config)

    assert content.startswith(NIX_HEADER)


def test_generate_is_valid_nix_function(generator: NixosGenerator) -> None:
    content = generator.generate(Config(version=CONFIG_VERSION))

    assert "{ config, pkgs, ... }:" in content
    assert content.rstrip().endswith("}")


def test_hostname_appears(generator: NixosGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="web-01", timezone="UTC", locale="en_US.UTF-8"),
    )

    content = generator.generate(config)

    assert 'networking.hostName = "web-01";' in content
    assert 'time.timeZone = "UTC";' in content
    assert 'i18n.defaultLocale = "en_US.UTF-8";' in content


def test_state_version_always_present(generator: NixosGenerator) -> None:
    content = generator.generate(Config(version=CONFIG_VERSION))

    assert "system.stateVersion" in content


def test_packages_block(generator: NixosGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        packages=PackagesConfig(install=["nginx", "curl"]),
    )

    content = generator.generate(config)

    assert "environment.systemPackages = with pkgs; [" in content
    assert "nginx" in content
    assert "curl" in content


def test_services_known(generator: NixosGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        services={
            "nginx": ServiceConfig(),
            "docker": ServiceConfig(),
        },
    )

    content = generator.generate(config)

    assert "services.nginx.enable = true;" in content
    assert "services.docker.enable = true;" in content


def test_services_unknown_are_commented(generator: NixosGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        services={"weird-service": ServiceConfig()},
    )

    content = generator.generate(config)

    assert "weird-service" in content
    assert "no NixOS mapping" in content


def test_users_block_with_ssh_key(generator: NixosGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        users=[
            UserConfig(
                name="admin",
                groups=["wheel"],
                ssh_key="ssh-ed25519 AAAA test",
                sudo=True,
            )
        ],
    )

    content = generator.generate(config)

    assert "users.users = {" in content
    assert "admin = {" in content
    assert "isNormalUser = true;" in content
    assert "wheel" in content
    assert "ssh-ed25519 AAAA test" in content


def test_users_shell_mapping(generator: NixosGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        users=[UserConfig(name="bob", shell="/bin/zsh")],
    )

    content = generator.generate(config)

    assert "shell = pkgs.zsh;" in content


def test_firewall_block(generator: NixosGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22, 80, 443]),
    )

    content = generator.generate(config)

    assert "networking.firewall = {" in content
    assert "enable = true;" in content
    assert "allowedTCPPorts = [ 22 80 443 ];" in content


def test_file_under_etc(generator: NixosGenerator, tmp_path: Path) -> None:
    source = tmp_path / "app.conf"
    source.write_text("hello = world\n", encoding="utf-8")

    config = Config(
        version=CONFIG_VERSION,
        files=[
            FileEntry(
                src=str(source),
                dest="/etc/myapp/app.conf",
                mode="0644",
            )
        ],
    )

    content = generator.generate(config)

    assert 'environment.etc."myapp/app.conf"' in content
    assert "hello = world" in content
    assert 'mode = "0644";' in content


def test_missing_file_source_placeholder(generator: NixosGenerator, tmp_path: Path) -> None:
    config = Config(
        version=CONFIG_VERSION,
        files=[FileEntry(src=str(tmp_path / "missing"), dest="/etc/x/y")],
    )

    content = generator.generate(config)

    assert "source not found" in content


def test_backend_write_creates_file(tmp_path: Path) -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="test"),
    )
    backend = NixosBackend()
    target = tmp_path / "configuration.nix"

    result = backend.write(config, target)

    assert result.exists()
    assert result.read_text(encoding="utf-8").startswith(NIX_HEADER)


def test_backend_supports_returns_false() -> None:
    backend = NixosBackend()
    task = Task(kind=TaskKind.SERVER, name="x")

    assert backend.supports(task) is False


def test_backend_run_returns_skipped() -> None:
    backend = NixosBackend()
    task = Task(kind=TaskKind.SERVER, name="x")
    result = backend.run(task, BackendContext(target_host="localhost"))

    assert result.status is TaskStatus.SKIPPED


def test_backend_name() -> None:
    assert NixosBackend().name == "nixos"


def test_generate_nixos_function() -> None:
    content = generate_nixos(Config(version=CONFIG_VERSION))

    assert "system.stateVersion" in content
