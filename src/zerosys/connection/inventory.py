from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import yaml

from zerosys.core.errors import ZeroSysError

DEFAULT_PORT = 22
INVENTORY_FILENAME = "inventory.yaml"


class InventoryError(ZeroSysError):
    pass


@dataclass(frozen=True)
class Host:
    name: str
    address: str
    user: str | None = None
    port: int = DEFAULT_PORT
    key_file: str | None = None
    tags: list[str] = field(default_factory=list)

    def target(self) -> str:
        if self.user:
            return f"{self.user}@{self.address}"
        return self.address


@dataclass
class Inventory:
    hosts: dict[str, Host] = field(default_factory=dict)

    def add(self, host: Host) -> None:
        self.hosts[host.name] = host

    def get(self, name: str) -> Host | None:
        return self.hosts.get(name)

    def remove(self, name: str) -> bool:
        return self.hosts.pop(name, None) is not None

    def names(self) -> list[str]:
        return sorted(self.hosts.keys())

    def by_tag(self, tag: str) -> list[Host]:
        return [h for h in self.hosts.values() if tag in h.tags]

    def __len__(self) -> int:
        return len(self.hosts)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self.hosts


def _parse_host(name: str, data: dict[str, object]) -> Host:
    address = data.get("address") or data.get("host")
    if not address:
        raise InventoryError(f"host '{name}' has no address")
    user = data.get("user")
    port_raw = data.get("port", DEFAULT_PORT)
    try:
        port = int(str(port_raw))
    except ValueError as exc:
        raise InventoryError(f"host '{name}' has invalid port: {port_raw}") from exc
    key_file = data.get("key_file") or data.get("ssh_key")
    tags_raw = data.get("tags", [])
    tags: list[str] = []
    if isinstance(tags_raw, list):
        tags = [str(t) for t in tags_raw]
    return Host(
        name=name,
        address=str(address),
        user=str(user) if user else None,
        port=port,
        key_file=str(key_file) if key_file else None,
        tags=tags,
    )


def parse_inventory(data: dict[str, object]) -> Inventory:
    inventory = Inventory()
    hosts_raw = data.get("hosts")
    if not isinstance(hosts_raw, dict):
        raise InventoryError("inventory must contain a 'hosts' mapping")
    for name, host_data in hosts_raw.items():
        if not isinstance(host_data, dict):
            raise InventoryError(f"host '{name}' must be a mapping")
        inventory.add(_parse_host(str(name), cast("dict[str, object]", host_data)))
    return inventory


def load_inventory(path: Path | str) -> Inventory:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise InventoryError(f"inventory not found: {target}")
    try:
        data = yaml.safe_load(target.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise InventoryError(f"cannot read {target}: {exc}") from exc
    if not isinstance(data, dict):
        raise InventoryError(f"inventory must be a mapping: {target}")
    return parse_inventory(data)


def dump_inventory(inventory: Inventory) -> str:
    hosts: dict[str, object] = {}
    for host in inventory.hosts.values():
        entry: dict[str, object] = {"address": host.address}
        if host.user:
            entry["user"] = host.user
        if host.port != DEFAULT_PORT:
            entry["port"] = host.port
        if host.key_file:
            entry["key_file"] = host.key_file
        if host.tags:
            entry["tags"] = host.tags
        hosts[host.name] = entry
    payload: dict[str, object] = {"hosts": hosts}
    return str(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
