from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass

from zerosys.core.errors import ZeroSysError


class NetworkError(ZeroSysError):
    pass


DEFAULT_TIMEOUT = 5.0


@dataclass(frozen=True)
class PortProbe:
    host: str
    port: int
    open: bool
    error: str = ""


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def is_private_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback


def resolve_hostname(hostname: str, timeout: float = DEFAULT_TIMEOUT) -> list[str]:
    socket.setdefaulttimeout(timeout)
    try:
        _, _, addresses = socket.gethostbyname_ex(hostname)
    except socket.gaierror as exc:
        raise NetworkError(f"cannot resolve {hostname}: {exc}") from exc
    return addresses


def probe_port(host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> PortProbe:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return PortProbe(host=host, port=port, open=True)
    except OSError as exc:
        return PortProbe(host=host, port=port, open=False, error=str(exc))


def local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1.0)
            sock.connect(("8.8.8.8", 80))
            raw = sock.getsockname()[0]
            return str(raw)
    except OSError:
        return "127.0.0.1"


def parse_host_port(value: str, default_port: int = 22) -> tuple[str, int]:
    if value.count(":") == 0:
        return value, default_port
    if value.startswith("["):
        end = value.find("]")
        if end == -1:
            raise NetworkError(f"invalid host syntax: {value}")
        host = value[1:end]
        rest = value[end + 1 :]
        if not rest.startswith(":"):
            return host, default_port
        return host, int(rest[1:])
    host, _, raw_port = value.rpartition(":")
    if not host:
        raise NetworkError(f"invalid host syntax: {value}")
    return host, int(raw_port)
