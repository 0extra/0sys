from __future__ import annotations

from typing import Any

from zerosys.core.config.schema import (
    CONFIG_VERSION,
    CommandEntry,
    Config,
    FileEntry,
    FirewallConfig,
    FirewallDefault,
    PackagesConfig,
    ServerConfig,
    ServiceConfig,
    UserConfig,
)

DEFAULT_CONFIG_FILENAME = "0sys.yaml"
DEFAULT_STATE_DIRNAME = ".0sys"

DEFAULT_SHELL = "/bin/bash"
DEFAULT_FILE_OWNER = "root"
DEFAULT_FILE_GROUP = "root"
DEFAULT_FILE_MODE = "0644"

DEFAULT_FIREWALL_DEFAULT: FirewallDefault = "deny"
DEFAULT_SSH_PORT = 22

DEFAULT_TIMEZONE = "UTC"
DEFAULT_LOCALE = "en_US.UTF-8"

BASE_PACKAGES_DEBIAN: list[str] = [
    "curl",
    "ca-certificates",
    "gnupg",
    "ufw",
    "fail2ban",
]

BASE_PACKAGES_ARCH: list[str] = [
    "curl",
    "ca-certificates",
    "ufw",
    "fail2ban",
]

BASE_PACKAGES_REDHAT: list[str] = [
    "curl",
    "ca-certificates",
    "gnupg2",
    "firewalld",
    "fail2ban",
]


def empty_config() -> Config:
    return Config(version=CONFIG_VERSION)


def minimal_config(hostname: str | None = None) -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(
            hostname=hostname,
            timezone=DEFAULT_TIMEZONE,
            locale=DEFAULT_LOCALE,
        ),
        firewall=FirewallConfig(
            default=DEFAULT_FIREWALL_DEFAULT,
            allow=[DEFAULT_SSH_PORT],
        ),
    )


def web_server_config(hostname: str | None = None) -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(
            hostname=hostname,
            timezone=DEFAULT_TIMEZONE,
            locale=DEFAULT_LOCALE,
        ),
        packages=PackagesConfig(install=["nginx", *BASE_PACKAGES_DEBIAN]),
        services={
            "nginx": ServiceConfig(state="started", enabled=True),
        },
        firewall=FirewallConfig(
            default=DEFAULT_FIREWALL_DEFAULT,
            allow=[DEFAULT_SSH_PORT, 80, 443],
        ),
    )


def docker_host_config(hostname: str | None = None) -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(
            hostname=hostname,
            timezone=DEFAULT_TIMEZONE,
            locale=DEFAULT_LOCALE,
        ),
        packages=PackagesConfig(install=["docker", "docker-compose", *BASE_PACKAGES_DEBIAN]),
        services={
            "docker": ServiceConfig(state="started", enabled=True),
        },
        firewall=FirewallConfig(
            default=DEFAULT_FIREWALL_DEFAULT,
            allow=[DEFAULT_SSH_PORT],
        ),
    )


def default_user(name: str, ssh_key: str | None = None) -> UserConfig:
    return UserConfig(
        name=name,
        groups=["sudo"],
        ssh_key=ssh_key,
        shell=DEFAULT_SHELL,
        sudo=True,
    )


def default_file(src: str, dest: str, mode: str = DEFAULT_FILE_MODE) -> FileEntry:
    return FileEntry(
        src=src,
        dest=dest,
        owner=DEFAULT_FILE_OWNER,
        group=DEFAULT_FILE_GROUP,
        mode=mode,
    )


def default_command(name: str, run: str) -> CommandEntry:
    return CommandEntry(name=name, run=run, when="once")


def package_list_for_os(os_id: str) -> list[str]:
    normalized = os_id.lower()
    if normalized in {"ubuntu", "debian", "linuxmint", "pop"}:
        return list(BASE_PACKAGES_DEBIAN)
    if normalized in {"arch", "manjaro", "endeavouros"}:
        return list(BASE_PACKAGES_ARCH)
    if normalized in {"fedora", "rhel", "centos", "rocky", "almalinux"}:
        return list(BASE_PACKAGES_REDHAT)
    return list(BASE_PACKAGES_DEBIAN)


def config_to_dict(config: Config) -> dict[str, Any]:
    return config.model_dump(exclude_unset=True, exclude_none=True)
