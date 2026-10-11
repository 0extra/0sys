from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from zerosys.core.errors import SecurityError
from zerosys.core.security.ssh import (
    check_private_key_permissions,
    detect_key_type,
    ensure_private_key_permissions,
    fingerprint,
    generate_keypair,
    is_valid_public_key,
    normalize_public_key,
    read_public_key,
)

pytestmark = pytest.mark.unit

SAMPLE_ED25519 = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHq6dAamSVjXbKqH1XYi6B7nYq5V2q8tBmV1npOcxzr9 user@example"
)

SAMPLE_RSA = (
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDh1wYu9zZKcNjdA0KZQvRykMcyB9FQy9uW"
    "eHhuGJdO1n3Ebqjm7oXvEw0HfwEJYlLYlLoCr6KwW3tQyHRFbLzU+Zq1W6L+tSfu3oZb"
    "MqE4Xpr9Z3F2Vx6pQcQ4ZqHkUjWlVgF5pExj3zW6Vt+xOGNlcF3zGfWQ3Fw=="
)


def test_is_valid_public_key_accepts_ed25519() -> None:
    assert is_valid_public_key(SAMPLE_ED25519) is True


def test_is_valid_public_key_accepts_rsa() -> None:
    assert is_valid_public_key(SAMPLE_RSA) is True


def test_is_valid_public_key_rejects_empty() -> None:
    assert is_valid_public_key("") is False


def test_is_valid_public_key_rejects_random_text() -> None:
    assert is_valid_public_key("hello world") is False


def test_detect_key_type_ed25519() -> None:
    assert detect_key_type(SAMPLE_ED25519) == "ssh-ed25519"


def test_detect_key_type_empty_raises() -> None:
    with pytest.raises(SecurityError):
        detect_key_type("")


def test_fingerprint_deterministic() -> None:
    first = fingerprint(SAMPLE_ED25519)
    second = fingerprint(SAMPLE_ED25519)

    assert first == second
    assert first.startswith("SHA256:")


def test_fingerprint_invalid_raises() -> None:
    with pytest.raises(SecurityError):
        fingerprint("not a key")


def test_normalize_with_new_comment() -> None:
    result = normalize_public_key(SAMPLE_ED25519, comment="new@host")

    assert result.endswith("new@host")


def test_normalize_without_comment_keeps_existing() -> None:
    result = normalize_public_key(SAMPLE_ED25519)

    assert "user@example" in result


def test_normalize_invalid_raises() -> None:
    with pytest.raises(SecurityError):
        normalize_public_key("bad key")


@pytest.mark.skipif(shutil.which("ssh-keygen") is None, reason="ssh-keygen not available")
def test_generate_keypair_creates_files(tmp_path: Path) -> None:
    destination = tmp_path / "id_ed25519"

    pair = generate_keypair(destination)

    assert pair.private_path.exists()
    assert pair.public_path.exists()
    assert pair.key_type == "ed25519"
    assert pair.fingerprint.startswith("SHA256:")


@pytest.mark.skipif(shutil.which("ssh-keygen") is None, reason="ssh-keygen not available")
def test_generate_keypair_refuses_overwrite(tmp_path: Path) -> None:
    destination = tmp_path / "id_ed25519"
    generate_keypair(destination)

    with pytest.raises(SecurityError, match="already exists"):
        generate_keypair(destination)


@pytest.mark.skipif(shutil.which("ssh-keygen") is None, reason="ssh-keygen not available")
def test_generate_keypair_overwrite_flag(tmp_path: Path) -> None:
    destination = tmp_path / "id_ed25519"
    generate_keypair(destination)

    pair = generate_keypair(destination, overwrite=True)

    assert pair.private_path.exists()


@pytest.mark.skipif(shutil.which("ssh-keygen") is None, reason="ssh-keygen not available")
def test_generate_keypair_sets_private_mode(tmp_path: Path) -> None:
    destination = tmp_path / "id_ed25519"
    pair = generate_keypair(destination)

    mode = pair.private_path.stat().st_mode & 0o777

    assert mode == 0o600


@pytest.mark.skipif(shutil.which("ssh-keygen") is None, reason="ssh-keygen not available")
def test_read_public_key_after_generate(tmp_path: Path) -> None:
    destination = tmp_path / "id_ed25519"
    pair = generate_keypair(destination)

    content = read_public_key(pair.public_path)

    assert content.startswith("ssh-ed25519")


def test_read_public_key_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        read_public_key(tmp_path / "missing.pub")


def test_check_private_key_permissions_true(tmp_path: Path) -> None:
    path = tmp_path / "key"
    path.write_text("data", encoding="utf-8")
    path.chmod(0o600)

    assert check_private_key_permissions(path) is True


def test_check_private_key_permissions_false(tmp_path: Path) -> None:
    path = tmp_path / "key"
    path.write_text("data", encoding="utf-8")
    path.chmod(0o644)

    assert check_private_key_permissions(path) is False


def test_ensure_private_key_permissions_fixes(tmp_path: Path) -> None:
    path = tmp_path / "key"
    path.write_text("data", encoding="utf-8")
    path.chmod(0o644)

    ensure_private_key_permissions(path)

    assert path.stat().st_mode & 0o777 == 0o600
