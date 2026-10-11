from __future__ import annotations

import base64
import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from zerosys.core.errors import SecurityError
from zerosys.core.security.permissions import PRIVATE_MODE, PUBLIC_MODE

KEY_PATTERN = re.compile(
    r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521) "
    r"([A-Za-z0-9+/=]+)(?: (.*))?$"
)

DEFAULT_KEY_TYPE = "ed25519"
DEFAULT_COMMENT = "0sys"


@dataclass(frozen=True)
class SshKeyPair:
    private_path: Path
    public_path: Path
    key_type: str
    fingerprint: str
    comment: str


def is_valid_public_key(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    if not stripped.startswith(("ssh-", "ecdsa-")):
        return False
    return KEY_PATTERN.match(stripped) is not None


def detect_key_type(public_key: str) -> str:
    parts = public_key.strip().split()
    if not parts:
        raise SecurityError("empty SSH key")
    return parts[0]


def fingerprint(public_key: str) -> str:
    stripped = public_key.strip()
    if not is_valid_public_key(stripped):
        raise SecurityError("invalid SSH public key format")
    parts = stripped.split()
    try:
        decoded = base64.b64decode(parts[1])
    except (ValueError, IndexError) as exc:
        raise SecurityError(f"cannot decode SSH key: {exc}") from exc
    digest = hashlib.sha256(decoded).digest()
    encoded = base64.b64encode(digest).decode("ascii").rstrip("=")
    return f"SHA256:{encoded}"


def normalize_public_key(public_key: str, comment: str | None = None) -> str:
    stripped = public_key.strip()
    if not is_valid_public_key(stripped):
        raise SecurityError("invalid SSH public key format")
    parts = stripped.split()
    if comment:
        return f"{parts[0]} {parts[1]} {comment}"
    if len(parts) >= 3:
        return f"{parts[0]} {parts[1]} {parts[2]}"
    return f"{parts[0]} {parts[1]}"


def check_private_key_permissions(path: Path) -> bool:
    if not path.exists():
        raise SecurityError(f"file not found: {path}")
    mode = path.stat().st_mode & 0o777
    return mode == PRIVATE_MODE


def ensure_private_key_permissions(path: Path) -> None:
    if not path.exists():
        raise SecurityError(f"file not found: {path}")
    path.chmod(PRIVATE_MODE)


def read_public_key(path: Path) -> str:
    target = path.expanduser().resolve()
    if not target.exists():
        raise SecurityError(f"file not found: {target}")
    content = target.read_text(encoding="utf-8").strip()
    if not is_valid_public_key(content):
        raise SecurityError(f"invalid public key in {target}")
    return content


def generate_keypair(
    destination: Path,
    key_type: str = DEFAULT_KEY_TYPE,
    comment: str = DEFAULT_COMMENT,
    overwrite: bool = False,
) -> SshKeyPair:
    private_path = destination.expanduser().resolve()
    public_path = private_path.with_suffix(private_path.suffix + ".pub")

    if private_path.exists():
        if not overwrite:
            raise SecurityError(f"key already exists: {private_path}")
        private_path.unlink()
    if public_path.exists():
        public_path.unlink()

    private_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ssh-keygen",
        "-t",
        key_type,
        "-f",
        str(private_path),
        "-N",
        "",
        "-C",
        comment,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise SecurityError(f"cannot run ssh-keygen: {exc}") from exc

    if completed.returncode != 0:
        raise SecurityError(f"ssh-keygen failed: {completed.stderr.strip()}")

    private_path.chmod(PRIVATE_MODE)
    if public_path.exists():
        public_path.chmod(PUBLIC_MODE)

    public_key = public_path.read_text(encoding="utf-8").strip()

    return SshKeyPair(
        private_path=private_path,
        public_path=public_path,
        key_type=key_type,
        fingerprint=fingerprint(public_key),
        comment=comment,
    )
