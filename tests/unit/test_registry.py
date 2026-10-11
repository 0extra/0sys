from __future__ import annotations

import pytest

from zerosys.backends.base import Backend, BackendContext
from zerosys.backends.registry import (
    BackendRegistry,
    backend_names,
    get_backend,
    get_registry,
    has_backend,
    load_default_backends,
    register_backend,
)
from zerosys.core.errors import BackendNotFoundError
from zerosys.core.planner.task import Task, TaskResult, TaskStatus

pytestmark = pytest.mark.unit


class _StubBackend(Backend):
    def __init__(self, name: str = "stub") -> None:
        self.name = name
        self.description = "stub backend"

    def supports(self, task: Task) -> bool:
        return True

    def run(self, task: Task, context: BackendContext) -> TaskResult:
        return TaskResult(status=TaskStatus.SUCCESS)


def test_register_and_get() -> None:
    registry = BackendRegistry()
    stub = _StubBackend("alpha")
    registry.register(stub)

    assert registry.get("alpha") is stub


def test_get_unknown_raises() -> None:
    registry = BackendRegistry()

    with pytest.raises(BackendNotFoundError):
        registry.get("missing")


def test_has_returns_true_for_registered() -> None:
    registry = BackendRegistry()
    registry.register(_StubBackend("beta"))

    assert registry.has("beta") is True
    assert registry.has("missing") is False


def test_names_are_sorted() -> None:
    registry = BackendRegistry()
    registry.register(_StubBackend("zulu"))
    registry.register(_StubBackend("alpha"))

    assert registry.names() == ["alpha", "zulu"]


def test_all_returns_registered_backends() -> None:
    registry = BackendRegistry()
    registry.register(_StubBackend("a"))
    registry.register(_StubBackend("b"))

    assert len(registry.all()) == 2


def test_clear_removes_everything() -> None:
    registry = BackendRegistry()
    registry.register(_StubBackend("x"))
    registry.clear()

    assert registry.names() == []


def test_default_registry_is_singleton() -> None:
    assert get_registry() is get_registry()


def test_register_backend_uses_global_registry() -> None:
    stub = _StubBackend("global-stub")
    register_backend(stub)
    try:
        assert has_backend("global-stub")
        assert get_backend("global-stub") is stub
        assert "global-stub" in backend_names()
    finally:
        get_registry()._backends.pop("global-stub", None)


def test_load_default_backends_registers_ansible_and_shell() -> None:
    registry = load_default_backends()

    assert registry.has("ansible")
    assert registry.has("shell")


def test_load_default_backends_is_idempotent() -> None:
    registry = load_default_backends()
    registry = load_default_backends()

    assert registry.names().count("ansible") == 1
    assert registry.names().count("shell") == 1
