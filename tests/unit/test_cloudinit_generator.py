from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from zerosys.backends.base import BackendContext
from zerosys.backends.cloudinit import (
    CLOUD_CONFIG_HEADER,
    CloudInitBackend,
    CloudInitGenerator,
)
from zerosys.core.config.schema import (
    CONFIG_VERSION,
    CommandEntry,
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
def generator() -> CloudInitGenerator:
    return CloudInitGenerator()


def _parse(content: str) -> dict[str, object]:
    assert content.startswith(CLOUD_CONFIG_HEADER)
    body = content[len(CLOUD_CONFIG_HEADER) :]
    data = yaml.safe_load(body)
    assert isinstance(data, dict)
    return data


def test_generate_starts_with_header(generator: CloudInitGenerator) -> None:
    config = Config(version=CONFIG_VERSION)

    content = generator.generate(config)

    assert content.startswith(CLOUD_CONFIG_HEADER)


def test_generate_empty_config_is_valid_yaml(generator: CloudInitGenerator) -> None:
    config = Config(version=CONFIG_VERSION)

    data = _parse(generator.generate(config))

    assert isinstance(data, dict)


def test_server_section_maps_hostname(generator: CloudInitGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="web-01", timezone="UTC", locale="en_US.UTF-8"),
    )

    data = _parse(generator.generate(config))

    assert data["hostname"] == "web-01"
    assert data["preserve_hostname"] is False
    assert data["timezone"] == "UTC"
    assert data["locale"] == "en_US.UTF-8"


def test_packages_section_lists_and_updates(generator: CloudInitGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        packages=PackagesConfig(install=["nginx", "ufw"]),
    )

    data = _parse(generator.generate(config))

    assert data["packages"] == ["nginx", "ufw"]
    assert data["package_update"] is True


def test_users_section_includes_sudo_and_key(generator: CloudInitGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        users=[
            UserConfig(
                name="admin",
                groups=["sudo"],
                shell="/bin/bash",
                sudo=True,
                ssh_key="ssh-ed25519 AAAA test",
            )
        ],
    )

    data = _parse(generator.generate(config))
    users = data["users"]
    assert isinstance(users, list)
    assert users[0]["name"] == "admin"
    assert users[0]["sudo"] == "ALL=(ALL) NOPASSWD:ALL"
    assert users[0]["ssh_authorized_keys"] == ["ssh-ed25519 AAAA test"]
    assert data["ssh_pwauth"] is False


def test_users_without_key_does_not_disable_password(
    generator: CloudInitGenerator,
) -> None:
    config = Config(
        version=CONFIG_VERSION,
        users=[UserConfig(name="guest", groups=[], shell="/bin/bash")],
    )

    data = _parse(generator.generate(config))

    assert "ssh_pwauth" not in data


def test_firewall_generates_ufw_commands(generator: CloudInitGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="deny", allow=[22, 80, 443]),
    )

    data = _parse(generator.generate(config))
    runcmd = data["runcmd"]
    assert isinstance(runcmd, list)
    assert "ufw default deny incoming" in runcmd
    assert "ufw allow 22/tcp" in runcmd
    assert "ufw allow 80/tcp" in runcmd
    assert "ufw allow 443/tcp" in runcmd
    assert "ufw --force enable" in runcmd


def test_firewall_allow_default(generator: CloudInitGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        firewall=FirewallConfig(default="allow", allow=[22]),
    )

    data = _parse(generator.generate(config))
    runcmd = data["runcmd"]
    assert "ufw default allow incoming" in runcmd


def test_services_generate_systemctl_lines(generator: CloudInitGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        services={"nginx": ServiceConfig(state="started", enabled=True)},
    )

    data = _parse(generator.generate(config))
    runcmd = data["runcmd"]
    assert "systemctl enable --now nginx" in runcmd


def test_service_stopped(generator: CloudInitGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        services={"nginx": ServiceConfig(state="stopped", enabled=False)},
    )

    data = _parse(generator.generate(config))
    runcmd = data["runcmd"]
    assert "systemctl stop nginx" in runcmd


def test_commands_are_in_runcmd(generator: CloudInitGenerator) -> None:
    config = Config(
        version=CONFIG_VERSION,
        commands=[CommandEntry(name="deploy", run="echo hello", when="once")],
    )

    data = _parse(generator.generate(config))
    runcmd = data["runcmd"]
    assert "echo hello" in runcmd


def test_files_are_embedded(generator: CloudInitGenerator, tmp_path: Path) -> None:
    source = tmp_path / "config.conf"
    source.write_text("hello = world\n", encoding="utf-8")

    config = Config(
        version=CONFIG_VERSION,
        files=[
            FileEntry(
                src=str(source),
                dest="/etc/app/config.conf",
                owner="root",
                group="root",
                mode="0644",
            )
        ],
    )

    data = _parse(generator.generate(config))
    write_files = data["write_files"]
    assert isinstance(write_files, list)
    assert write_files[0]["path"] == "/etc/app/config.conf"
    assert "hello = world" in write_files[0]["content"]
    assert write_files[0]["owner"] == "root:root"


def test_missing_source_produces_placeholder(generator: CloudInitGenerator, tmp_path: Path) -> None:
    config = Config(
        version=CONFIG_VERSION,
        files=[
            FileEntry(
                src=str(tmp_path / "missing.conf"),
                dest="/etc/app/x.conf",
            )
        ],
    )

    data = _parse(generator.generate(config))
    write_files = data["write_files"]
    assert "source not found" in write_files[0]["content"]


def test_backend_write_creates_file(tmp_path: Path) -> None:
    config = Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="test"),
    )
    backend = CloudInitBackend()
    target = tmp_path / "user-data.yaml"

    result = backend.write(config, target)

    assert result.exists()
    assert result.read_text(encoding="utf-8").startswith(CLOUD_CONFIG_HEADER)


def test_backend_supports_returns_false() -> None:
    backend = CloudInitBackend()
    task = Task(kind=TaskKind.SERVER, name="x")

    assert backend.supports(task) is False


def test_backend_run_returns_skipped() -> None:
    backend = CloudInitBackend()
    task = Task(kind=TaskKind.SERVER, name="x")
    result = backend.run(task, BackendContext(target_host="localhost"))

    assert result.status is TaskStatus.SKIPPED


def test_backend_name() -> None:
    assert CloudInitBackend().name == "cloudinit"
