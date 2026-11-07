from __future__ import annotations

import pytest

from zerosys.backends.ansible.backend import ROLLBACK_KINDS, AnsibleBackend
from zerosys.core.planner.task import Task, TaskKind

pytestmark = pytest.mark.unit


@pytest.fixture
def backend() -> AnsibleBackend:
    return AnsibleBackend()


def test_supports_ansible_kinds(backend: AnsibleBackend) -> None:
    for kind in (
        TaskKind.SERVER,
        TaskKind.PACKAGES_INSTALL,
        TaskKind.PACKAGES_REMOVE,
        TaskKind.SERVICE,
        TaskKind.USER,
        TaskKind.FIREWALL,
        TaskKind.FILE,
        TaskKind.PROXY,
    ):
        task = Task(kind=kind, name=f"t_{kind.value}")
        assert backend.supports(task) is True


def test_does_not_support_command(backend: AnsibleBackend) -> None:
    task = Task(kind=TaskKind.COMMAND, name="c")
    assert backend.supports(task) is False


def test_can_rollback_matches_rollback_kinds(backend: AnsibleBackend) -> None:
    for kind in ROLLBACK_KINDS:
        task = Task(kind=kind, name=f"t_{kind.value}")
        assert backend.can_rollback(task) is True

    for kind in (TaskKind.SERVER, TaskKind.FIREWALL, TaskKind.PROXY, TaskKind.COMMAND):
        task = Task(kind=kind, name=f"t_{kind.value}")
        assert backend.can_rollback(task) is False


RECAP_CHANGED_2 = (
    "PLAY RECAP *********************************************************************\n"
    "localhost                  : ok=4    changed=2    unreachable=0    failed=0    "
    "skipped=1    rescued=0    ignored=0\n"
)

RECAP_CHANGED_0 = (
    "PLAY RECAP *********************************************************************\n"
    "localhost                  : ok=4    changed=0    unreachable=0    failed=0    "
    "skipped=1    rescued=0    ignored=0\n"
)

RECAP_MULTI_HOST = (
    "PLAY RECAP *********************************************************************\n"
    "web-01                     : ok=4    changed=1    unreachable=0    failed=0    "
    "skipped=0    rescued=0    ignored=0\n"
    "web-02                     : ok=4    changed=2    unreachable=0    failed=0    "
    "skipped=0    rescued=0    ignored=0\n"
)


def test_was_changed_recap_reports_changes(backend: AnsibleBackend) -> None:
    assert backend._was_changed({}, RECAP_CHANGED_2) is True


def test_was_changed_recap_reports_zero(backend: AnsibleBackend) -> None:
    assert backend._was_changed({}, RECAP_CHANGED_0) is False


def test_was_changed_recap_multi_host(backend: AnsibleBackend) -> None:
    assert backend._was_changed({}, RECAP_MULTI_HOST) is True


def test_was_changed_recap_takes_precedence_over_stats(backend: AnsibleBackend) -> None:
    stats = {"changed": 5}
    assert backend._was_changed(stats, RECAP_CHANGED_0) is False


def test_was_changed_flat_format_with_changes(backend: AnsibleBackend) -> None:
    stats = {"changed": 2, "ok": 4, "failed": 0}
    assert backend._was_changed(stats) is True


def test_was_changed_flat_format_no_changes(backend: AnsibleBackend) -> None:
    stats = {"changed": 0, "ok": 4, "failed": 0}
    assert backend._was_changed(stats) is False


def test_was_changed_nested_format_with_changes(backend: AnsibleBackend) -> None:
    stats = {"localhost": {"changed": 1, "ok": 3}}
    assert backend._was_changed(stats) is True


def test_was_changed_nested_format_no_changes(backend: AnsibleBackend) -> None:
    stats = {"localhost": {"changed": 0, "ok": 3}}
    assert backend._was_changed(stats) is False


def test_was_changed_category_format_with_changes(backend: AnsibleBackend) -> None:
    stats = {
        "ok": {"localhost": 4},
        "changed": {"localhost": 2},
        "skipped": {"localhost": 1},
    }
    assert backend._was_changed(stats) is True


def test_was_changed_category_format_zero(backend: AnsibleBackend) -> None:
    stats = {
        "ok": {"localhost": 4},
        "changed": {"localhost": 0},
        "skipped": {"localhost": 1},
    }
    assert backend._was_changed(stats) is False


def test_was_changed_multi_host_any_changed(backend: AnsibleBackend) -> None:
    stats = {
        "web-01": {"changed": 0, "ok": 3},
        "web-02": {"changed": 2, "ok": 3},
    }
    assert backend._was_changed(stats) is True


def test_was_changed_multi_host_none_changed(backend: AnsibleBackend) -> None:
    stats = {
        "web-01": {"changed": 0, "ok": 3},
        "web-02": {"changed": 0, "ok": 3},
    }
    assert backend._was_changed(stats) is False


def test_was_changed_empty_stats_no_stdout_is_false(backend: AnsibleBackend) -> None:
    assert backend._was_changed({}) is False


def test_was_changed_ignores_non_int_changed(backend: AnsibleBackend) -> None:
    stats = {"localhost": {"changed": "yes"}}
    assert backend._was_changed(stats) is False


def test_was_changed_ignores_non_dict_host_stats(backend: AnsibleBackend) -> None:
    stats = {"localhost": "some string", "other": 42}
    assert backend._was_changed(stats) is False
