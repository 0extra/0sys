from __future__ import annotations

from zerosys.backends.base import Backend
from zerosys.core.errors import BackendNotFoundError


class BackendRegistry:
    def __init__(self) -> None:
        self._backends: dict[str, Backend] = {}

    def register(self, backend: Backend) -> None:
        self._backends[backend.name] = backend

    def get(self, name: str) -> Backend:
        try:
            return self._backends[name]
        except KeyError as exc:
            raise BackendNotFoundError(f"backend '{name}' is not registered") from exc

    def has(self, name: str) -> bool:
        return name in self._backends

    def names(self) -> list[str]:
        return sorted(self._backends.keys())

    def all(self) -> list[Backend]:
        return list(self._backends.values())

    def clear(self) -> None:
        self._backends.clear()


_registry = BackendRegistry()


def get_registry() -> BackendRegistry:
    return _registry


def register_backend(backend: Backend) -> None:
    _registry.register(backend)


def get_backend(name: str) -> Backend:
    return _registry.get(name)


def has_backend(name: str) -> bool:
    return _registry.has(name)


def backend_names() -> list[str]:
    return _registry.names()


def load_default_backends() -> BackendRegistry:
    from zerosys.backends.ansible.backend import AnsibleBackend
    from zerosys.backends.shell.backend import ShellBackend

    if not _registry.has("ansible"):
        _registry.register(AnsibleBackend())
    if not _registry.has("shell"):
        _registry.register(ShellBackend())
    return _registry
