from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from zerosys.connection.inventory import (
    DEFAULT_PORT,
    Host,
    Inventory,
    InventoryError,
    dump_inventory,
    load_inventory,
    parse_inventory,
)

pytestmark = pytest.mark.unit


def test_host_default_port() -> None:
    host = Host(name="web", address="1.2.3.4")

    assert host.port == DEFAULT_PORT


def test_host_target_with_user() -> None:
    host = Host(name="web", address="1.2.3.4", user="admin")

    assert host.target() == "admin@1.2.3.4"


def test_host_target_without_user() -> None:
    host = Host(name="web", address="1.2.3.4")

    assert host.target() == "1.2.3.4"


def test_inventory_add_and_get() -> None:
    inv = Inventory()
    host = Host(name="web", address="1.2.3.4")
    inv.add(host)

    assert inv.get("web") is host
    assert "web" in inv


def test_inventory_remove() -> None:
    inv = Inventory()
    inv.add(Host(name="web", address="1.2.3.4"))

    assert inv.remove("web") is True
    assert inv.remove("web") is False


def test_inventory_by_tag() -> None:
    inv = Inventory()
    inv.add(Host(name="a", address="1.1.1.1", tags=["web"]))
    inv.add(Host(name="b", address="2.2.2.2", tags=["db"]))
    inv.add(Host(name="c", address="3.3.3.3", tags=["web"]))

    assert [h.name for h in inv.by_tag("web")] == ["a", "c"]


def test_parse_inventory() -> None:
    data = {
        "hosts": {
            "web-01": {
                "address": "192.168.1.10",
                "user": "admin",
                "port": 2222,
                "tags": ["web", "prod"],
            }
        }
    }
    inv = parse_inventory(data)

    assert len(inv) == 1
    host = inv.get("web-01")
    assert host is not None
    assert host.user == "admin"
    assert host.port == 2222
    assert "prod" in host.tags


def test_parse_inventory_missing_hosts() -> None:
    with pytest.raises(InventoryError, match="hosts"):
        parse_inventory({})


def test_parse_inventory_missing_address() -> None:
    with pytest.raises(InventoryError, match="address"):
        parse_inventory({"hosts": {"web": {"user": "x"}}})


def test_parse_inventory_invalid_port() -> None:
    with pytest.raises(InventoryError, match="port"):
        parse_inventory({"hosts": {"web": {"address": "1.1.1.1", "port": "abc"}}})


def test_load_inventory(tmp_path: Path) -> None:
    path = tmp_path / "inv.yaml"
    path.write_text(
        yaml.safe_dump({"hosts": {"web": {"address": "1.1.1.1"}}}),
        encoding="utf-8",
    )

    inv = load_inventory(path)

    assert "web" in inv


def test_load_missing_file(tmp_path: Path) -> None:
    with pytest.raises(InventoryError):
        load_inventory(tmp_path / "missing.yaml")


def test_dump_then_load_roundtrip() -> None:
    inv = Inventory()
    inv.add(Host(name="a", address="1.1.1.1", user="admin", port=2222, tags=["web"]))

    text = dump_inventory(inv)
    data = yaml.safe_load(text)
    restored = parse_inventory(data)

    assert "a" in restored
    host = restored.get("a")
    assert host is not None
    assert host.port == 2222
