from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.backends.ansible.runner import AnsibleRunner

pytestmark = pytest.mark.unit


def test_localhost_default_port_no_key_is_local() -> None:
    runner = AnsibleRunner(inventory_host="localhost")
    inventory = runner._build_inventory()
    host_vars = inventory["all"]["hosts"]["localhost"]

    assert host_vars["ansible_connection"] == "local"


def test_localhost_with_ssh_key_uses_ssh() -> None:
    runner = AnsibleRunner(inventory_host="localhost", ssh_key="/tmp/key")
    inventory = runner._build_inventory()
    host_vars = inventory["all"]["hosts"]["localhost"]

    assert "ansible_connection" not in host_vars
    assert host_vars["ansible_ssh_private_key_file"] == "/tmp/key"


def test_localhost_with_nonstandard_port_uses_ssh() -> None:
    runner = AnsibleRunner(inventory_host="localhost", inventory_port=2222)
    inventory = runner._build_inventory()
    host_vars = inventory["all"]["hosts"]["localhost"]

    assert "ansible_connection" not in host_vars
    assert host_vars["ansible_port"] == 2222


def test_localhost_with_user_uses_ssh() -> None:
    runner = AnsibleRunner(inventory_host="localhost", inventory_user="testuser")
    inventory = runner._build_inventory()
    host_vars = inventory["all"]["hosts"]["localhost"]

    assert "ansible_connection" not in host_vars
    assert host_vars["ansible_user"] == "testuser"


def test_remote_host_always_uses_ssh() -> None:
    runner = AnsibleRunner(inventory_host="192.0.2.10", inventory_user="admin")
    inventory = runner._build_inventory()
    host_vars = inventory["all"]["hosts"]["192.0.2.10"]

    assert "ansible_connection" not in host_vars
    assert host_vars["ansible_user"] == "admin"


def test_ssh_inventory_includes_known_hosts_args() -> None:
    runner = AnsibleRunner(
        inventory_host="localhost",
        inventory_port=2222,
        ssh_key="/tmp/key",
        known_hosts_file=Path("/tmp/known_hosts"),
    )
    inventory = runner._build_inventory()
    host_vars = inventory["all"]["hosts"]["localhost"]

    assert "ansible_ssh_common_args" in host_vars
    assert "UserKnownHostsFile=/tmp/known_hosts" in host_vars["ansible_ssh_common_args"]
    assert "StrictHostKeyChecking=accept-new" in host_vars["ansible_ssh_common_args"]


def test_strict_host_key_changes_check_mode() -> None:
    runner = AnsibleRunner(
        inventory_host="localhost",
        inventory_port=2222,
        ssh_key="/tmp/key",
        strict_host_key=True,
    )
    inventory = runner._build_inventory()
    host_vars = inventory["all"]["hosts"]["localhost"]

    assert "StrictHostKeyChecking=yes" in host_vars["ansible_ssh_common_args"]
