from __future__ import annotations

from collections.abc import Callable
from typing import Any

from zerosys.core.config.schema import CONFIG_VERSION, Config
from zerosys.core.errors import ConfigVersionError

MigrationFunc = Callable[[dict[str, Any]], dict[str, Any]]


MIGRATIONS: dict[int, MigrationFunc] = {}


def register_migration(from_version: int) -> Callable[[MigrationFunc], MigrationFunc]:
    def decorator(func: MigrationFunc) -> MigrationFunc:
        MIGRATIONS[from_version] = func
        return func

    return decorator


def detect_version(data: dict[str, Any]) -> int:
    version = data.get("version")
    if version is None:
        return 0
    if not isinstance(version, int):
        raise ConfigVersionError(f"config version must be an integer, got {type(version).__name__}")
    return version


def migrate(data: dict[str, Any]) -> dict[str, Any]:
    current = dict(data)
    version = detect_version(current)

    if version == CONFIG_VERSION:
        return current

    if version > CONFIG_VERSION:
        raise ConfigVersionError(
            f"config version {version} is newer than supported {CONFIG_VERSION}; "
            f"please upgrade 0sys"
        )

    while version < CONFIG_VERSION:
        migration = MIGRATIONS.get(version)
        if migration is None:
            raise ConfigVersionError(
                f"no migration path from version {version} to {CONFIG_VERSION}"
            )
        current = migration(current)
        new_version = detect_version(current)
        if new_version <= version:
            raise ConfigVersionError(
                f"migration from {version} did not advance version, got {new_version}"
            )
        version = new_version

    return current


def migrate_config(data: dict[str, Any]) -> Config:
    migrated = migrate(data)
    return Config.model_validate(migrated)
