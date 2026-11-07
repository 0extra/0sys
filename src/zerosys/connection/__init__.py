from __future__ import annotations

from zerosys.connection.local import (
    ConnectionError,
    ConnectionResult,
    LocalConnection,
)
from zerosys.connection.ssh import SSH_PORT_DEFAULT, SshConnection

__all__ = [
    "SSH_PORT_DEFAULT",
    "ConnectionError",
    "ConnectionResult",
    "LocalConnection",
    "SshConnection",
]
