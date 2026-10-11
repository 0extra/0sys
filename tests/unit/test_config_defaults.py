from __future__ import annotations

import pytest

from zerosys.core.config.defaults import (
    BASE_PACKAGES_ARCH,
    BASE_PACKAGES_DEBIAN,
    BASE_PACKAGES_REDHAT,
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_SSH_PORT,
    config_to_dict,
    default_command,
    default_file,
    default_user,
    docker_host_config,
    empty_config,
    minimal_config,
    package_list_for_os,
    web_server_config,
)

pytestmark = pytest.mark.unit


def test_empty_config_has_only_version() -> None:
    config = empty_config()

    assert config.version == 1
    assert config.server is None
    assert config.firewall is None
    assert config.packages is None


def test_minimal_config_has_server_and_firewall() -> None:
    config = minimal_config(hostname="my-vps")

    assert config.server is not None
    assert config.server.hostname == "my-vps"
    assert config.firewall is not None
    assert config.firewall.allow == [DEFAULT_SSH_PORT]


def test_minimal_config_without_hostname() -> None:
    config = minimal_config()

    assert config.server is not None
    assert config.server.hostname is None


def test_web_server_config_opens_http_ports() -> None:
    config = web_server_config(hostname="web-01")

    assert config.packages is not None
    assert "nginx" in config.packages.install
    assert config.firewall is not None
    assert 80 in config.firewall.allow
    assert 443 in config.firewall.allow
    assert "nginx" in config.services


def test_docker_host_config_installs_docker() -> None:
    config = docker_host_config(hostname="docker-01")

    assert config.packages is not None
    assert "docker" in config.packages.install
    assert "docker" in config.services
    assert config.firewall is not None
    assert 80 not in config.firewall.allow


def test_default_user_has_sudo_group() -> None:
    user = default_user("alice", ssh_key="ssh-rsa AAAA")

    assert user.name == "alice"
    assert "sudo" in user.groups
    assert user.sudo is True
    assert user.ssh_key == "ssh-rsa AAAA"


def test_default_file_sets_mode_and_owner() -> None:
    entry = default_file("./src.conf", "/etc/app/app.conf")

    assert entry.src == "./src.conf"
    assert entry.dest == "/etc/app/app.conf"
    assert entry.owner == "root"
    assert entry.mode == "0644"


def test_default_command_defaults_to_once() -> None:
    cmd = default_command("deploy", "echo hello")

    assert cmd.name == "deploy"
    assert cmd.run == "echo hello"
    assert cmd.when == "once"


@pytest.mark.parametrize(
    ("os_id", "expected"),
    [
        ("ubuntu", BASE_PACKAGES_DEBIAN),
        ("debian", BASE_PACKAGES_DEBIAN),
        ("Ubuntu", BASE_PACKAGES_DEBIAN),
        ("arch", BASE_PACKAGES_ARCH),
        ("manjaro", BASE_PACKAGES_ARCH),
        ("fedora", BASE_PACKAGES_REDHAT),
        ("rhel", BASE_PACKAGES_REDHAT),
        ("unknown-os", BASE_PACKAGES_DEBIAN),
    ],
)
def test_package_list_for_os(os_id: str, expected: list[str]) -> None:
    assert package_list_for_os(os_id) == expected


def test_config_to_dict_drops_unset_fields() -> None:
    config = minimal_config(hostname="x")
    payload = config_to_dict(config)

    assert "server" in payload
    assert "firewall" in payload
    assert "files" not in payload


def test_default_config_filename_is_yaml() -> None:
    assert DEFAULT_CONFIG_FILENAME.endswith(".yaml")
