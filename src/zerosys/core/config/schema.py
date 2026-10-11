from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CONFIG_VERSION = 1

ServiceState = Literal["started", "stopped", "restarted", "reloaded"]
FirewallDefault = Literal["allow", "deny"]
CommandWhen = Literal["always", "once", "changed"]


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    hostname: Annotated[str, Field(min_length=1, max_length=253)] | None = None
    timezone: str | None = None
    locale: str | None = None

    @field_validator("hostname")
    @classmethod
    def _validate_hostname(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("hostname cannot start or end with a dash")
        if ".." in v:
            raise ValueError("hostname cannot contain consecutive dots")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
        if not set(v).issubset(allowed):
            raise ValueError("hostname contains invalid characters")
        return v.lower()


class PackagesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    install: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)

    @field_validator("install", "remove")
    @classmethod
    def _deduplicate(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v))


class ServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: ServiceState = "started"
    enabled: bool = True
    config_file: str | None = None


class UserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Annotated[str, Field(min_length=1, max_length=32)]
    groups: list[str] = Field(default_factory=list)
    ssh_key: str | None = None
    shell: str = "/bin/bash"
    sudo: bool = False

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("user name must contain only letters, digits, dash and underscore")
        if v[0].isdigit():
            raise ValueError("user name cannot start with a digit")
        return v

    @field_validator("groups")
    @classmethod
    def _deduplicate_groups(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v))


class FirewallConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default: FirewallDefault = "deny"
    allow: list[int] = Field(default_factory=list)

    @field_validator("allow")
    @classmethod
    def _validate_ports(cls, v: list[int]) -> list[int]:
        for port in v:
            if port < 1 or port > 65535:
                raise ValueError(f"port {port} is out of range 1-65535")
        return sorted(set(v))


InfrastructureProvider = Literal["hetzner", "digitalocean"]


class InfrastructureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    provider: InfrastructureProvider
    region: Annotated[str, Field(min_length=1, max_length=64)]
    server_type: Annotated[str, Field(min_length=1, max_length=64)]
    image: str = "ubuntu-24.04"
    name: Annotated[str, Field(min_length=1, max_length=64)] | None = None
    ssh_keys: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("ssh_keys", "tags")
    @classmethod
    def _deduplicate(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v))


ProxyRuntime = Literal["docker"]
ProxyLogLevel = Literal["debug", "info", "warn", "error"]


class ProxyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    enabled: bool = False
    runtime: ProxyRuntime = "docker"
    port: Annotated[int, Field(ge=1, le=65535)] = 8443
    sni: Annotated[str, Field(min_length=1, max_length=253)] = "www.microsoft.com"
    max_connections: Annotated[int, Field(ge=1, le=65535)] = 512
    log_level: ProxyLogLevel = "info"
    version: str = "0.1.5"
    install_dir: str = "/opt/0tpe"
    ssh_keys: list[str] = Field(default_factory=list)

    @field_validator("ssh_keys")
    @classmethod
    def _deduplicate(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v))


class FileEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    src: str
    dest: str
    owner: str = "root"
    group: str = "root"
    mode: str = "0644"

    @field_validator("mode")
    @classmethod
    def _validate_mode(cls, v: str) -> str:
        if len(v) not in (3, 4) or any(c not in "01234567" for c in v):
            raise ValueError("mode must be an octal string like '0644' or '644'")
        return v


class CommandEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Annotated[str, Field(min_length=1)]
    run: Annotated[str, Field(min_length=1)]
    when: CommandWhen = "once"


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = CONFIG_VERSION
    server: ServerConfig | None = None
    packages: PackagesConfig | None = None
    services: dict[str, ServiceConfig] = Field(default_factory=dict)
    users: list[UserConfig] = Field(default_factory=list)
    firewall: FirewallConfig | None = None
    infrastructure: InfrastructureConfig | None = None
    proxy: ProxyConfig | None = None
    files: list[FileEntry] = Field(default_factory=list)
    commands: list[CommandEntry] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: int) -> int:
        if v != CONFIG_VERSION:
            raise ValueError(f"unsupported config version {v}, expected {CONFIG_VERSION}")
        return v

    @field_validator("services")
    @classmethod
    def _validate_service_names(cls, v: dict[str, ServiceConfig]) -> dict[str, ServiceConfig]:
        for name in v:
            if not name or not name.replace("-", "").replace("_", "").replace(".", "").isalnum():
                raise ValueError(f"invalid service name: {name}")
        return v

    @model_validator(mode="after")
    def _validate_unique_users(self) -> Config:
        names = [u.name for u in self.users]
        if len(names) != len(set(names)):
            raise ValueError("duplicate user names in config")
        return self

    @model_validator(mode="after")
    def _validate_unique_file_destinations(self) -> Config:
        dests = [f.dest for f in self.files]
        if len(dests) != len(set(dests)):
            raise ValueError("duplicate file destinations in config")
        return self
