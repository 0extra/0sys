from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from zerosys.core.config.schema import (
    CONFIG_VERSION,
    Config,
    FirewallConfig,
    PackagesConfig,
    ServerConfig,
    ServiceConfig,
    UserConfig,
)
from zerosys.core.state import StateStore


@pytest.fixture
def tmp_config_path(tmp_path: Path) -> Path:
    return tmp_path / "0sys.yaml"


@pytest.fixture
def minimal_yaml() -> str:
    return """\
version: 1
server:
  hostname: test-server
  timezone: UTC
  locale: en_US.UTF-8
firewall:
  default: deny
  allow: [22]
"""


@pytest.fixture
def web_yaml() -> str:
    return """\
version: 1
server:
  hostname: web-01
  timezone: UTC
packages:
  install: [nginx, ufw]
services:
  nginx:
    state: started
    enabled: true
firewall:
  default: deny
  allow: [22, 80, 443]
"""


@pytest.fixture
def docker_yaml() -> str:
    return """\
version: 1
server:
  hostname: docker-01
packages:
  install: [docker, docker-compose, ufw]
services:
  docker:
    state: started
    enabled: true
firewall:
  default: deny
  allow: [22]
"""


@pytest.fixture
def sample_config() -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(
            hostname="test-server",
            timezone="UTC",
            locale="en_US.UTF-8",
        ),
        firewall=FirewallConfig(default="deny", allow=[22]),
    )


@pytest.fixture
def web_config() -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="web-01", timezone="UTC"),
        packages=PackagesConfig(install=["nginx", "ufw"]),
        services={"nginx": ServiceConfig(state="started", enabled=True)},
        firewall=FirewallConfig(default="deny", allow=[22, 80, 443]),
    )


@pytest.fixture
def docker_config() -> Config:
    return Config(
        version=CONFIG_VERSION,
        server=ServerConfig(hostname="docker-01"),
        packages=PackagesConfig(install=["docker", "docker-compose", "ufw"]),
        services={"docker": ServiceConfig(state="started", enabled=True)},
        firewall=FirewallConfig(default="deny", allow=[22]),
    )


@pytest.fixture
def user_config() -> UserConfig:
    return UserConfig(
        name="admin",
        groups=["sudo"],
        shell="/bin/bash",
        sudo=True,
    )


@pytest.fixture
def store(tmp_path: Path) -> Iterator[StateStore]:
    instance = StateStore(tmp_path / "state.db")
    instance.connect()
    try:
        yield instance
    finally:
        instance.close()
