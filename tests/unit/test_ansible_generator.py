from __future__ import annotations

import pytest

from zerosys.backends.ansible.generator import PlaybookGenerator
from zerosys.core.planner.task import Task, TaskKind

pytestmark = pytest.mark.unit


@pytest.fixture
def generator() -> PlaybookGenerator:
    return PlaybookGenerator()


def test_build_playbook_has_single_play(generator: PlaybookGenerator) -> None:
    task = Task(kind=TaskKind.SERVER, name="s", params={"hostname": "x"})
    playbook = generator.build_playbook([task])

    assert len(playbook) == 1
    assert playbook[0]["hosts"] == "all"
    assert playbook[0]["become"] is True
    assert len(playbook[0]["tasks"]) == 1


def test_server_task_uses_base_role(generator: PlaybookGenerator) -> None:
    task = Task(
        kind=TaskKind.SERVER,
        name="s",
        params={"hostname": "my-vps", "timezone": "UTC", "locale": "en_US.UTF-8"},
    )
    playbook = generator.build_playbook([task])
    entry = playbook[0]["tasks"][0]

    assert entry["role"] == "base"
    assert entry["vars"]["server_hostname"] == "my-vps"
    assert entry["vars"]["server_timezone"] == "UTC"


def test_packages_install_uses_packages_role(generator: PlaybookGenerator) -> None:
    task = Task(
        kind=TaskKind.PACKAGES_INSTALL,
        name="p",
        params={"packages": ["nginx", "ufw"]},
    )
    playbook = generator.build_playbook([task])
    entry = playbook[0]["tasks"][0]

    assert entry["role"] == "packages"
    assert entry["vars"]["packages_install"] == ["nginx", "ufw"]


def test_packages_remove_uses_inline_module(generator: PlaybookGenerator) -> None:
    task = Task(
        kind=TaskKind.PACKAGES_REMOVE,
        name="p",
        params={"packages": ["apache2"]},
    )
    playbook = generator.build_playbook([task])
    entry = playbook[0]["tasks"][0]

    assert "role" not in entry
    assert entry["ansible.builtin.package"]["state"] == "absent"
    assert entry["ansible.builtin.package"]["name"] == ["apache2"]


def test_service_task_uses_service_role(generator: PlaybookGenerator) -> None:
    task = Task(
        kind=TaskKind.SERVICE,
        name="svc",
        params={
            "name": "nginx",
            "state": "started",
            "enabled": True,
            "config_file": None,
        },
    )
    playbook = generator.build_playbook([task])
    entry = playbook[0]["tasks"][0]

    assert entry["role"] == "service"
    assert entry["vars"]["service_name"] == "nginx"
    assert entry["vars"]["service_state"] == "started"


def test_user_task_uses_users_role(generator: PlaybookGenerator) -> None:
    task = Task(
        kind=TaskKind.USER,
        name="u",
        params={
            "name": "admin",
            "groups": ["sudo"],
            "ssh_key": "ssh-rsa AAAA",
            "shell": "/bin/bash",
            "sudo": True,
        },
    )
    playbook = generator.build_playbook([task])
    entry = playbook[0]["tasks"][0]

    assert entry["role"] == "users"
    assert entry["vars"]["user_name"] == "admin"
    assert entry["vars"]["user_sudo"] is True


def test_firewall_task_uses_firewall_role(generator: PlaybookGenerator) -> None:
    task = Task(
        kind=TaskKind.FIREWALL,
        name="fw",
        params={"default": "deny", "allow": [22, 80]},
    )
    playbook = generator.build_playbook([task])
    entry = playbook[0]["tasks"][0]

    assert entry["role"] == "firewall"
    assert entry["vars"]["firewall_default"] == "deny"
    assert entry["vars"]["firewall_allow"] == [22, 80]


def test_file_task_uses_file_role(generator: PlaybookGenerator) -> None:
    task = Task(
        kind=TaskKind.FILE,
        name="f",
        params={
            "src": "./x.conf",
            "dest": "/etc/app/x.conf",
            "owner": "root",
            "group": "root",
            "mode": "0644",
        },
    )
    playbook = generator.build_playbook([task])
    entry = playbook[0]["tasks"][0]

    assert entry["role"] == "file"
    assert entry["vars"]["file_dest"] == "/etc/app/x.conf"
    assert entry["vars"]["file_mode"] == "0644"


def test_tags_include_task_kind(generator: PlaybookGenerator) -> None:
    task = Task(kind=TaskKind.SERVER, name="s", params={"hostname": "x"})
    playbook = generator.build_playbook([task])
    entry = playbook[0]["tasks"][0]

    assert TaskKind.SERVER.value in entry["tags"]


def test_multiple_tasks_in_one_play(generator: PlaybookGenerator) -> None:
    tasks = [
        Task(kind=TaskKind.SERVER, name="s", params={"hostname": "x"}),
        Task(kind=TaskKind.FIREWALL, name="fw", params={"allow": [22]}),
    ]
    playbook = generator.build_playbook(tasks)

    assert len(playbook[0]["tasks"]) == 2


def test_custom_host_pattern(generator: PlaybookGenerator) -> None:
    task = Task(kind=TaskKind.SERVER, name="s", params={"hostname": "x"})
    playbook = generator.build_playbook([task], host_pattern="web-servers")

    assert playbook[0]["hosts"] == "web-servers"
