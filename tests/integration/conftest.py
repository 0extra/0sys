from __future__ import annotations

import subprocess
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from testcontainers.core.container import DockerContainer

try:
    import docker as _docker_sdk

    _DOCKER_AVAILABLE = True
except ImportError:
    _docker_sdk = None
    _DOCKER_AVAILABLE = False


@dataclass(frozen=True)
class SshTarget:
    host: str
    port: int
    user: str
    key_path: Path
    container_id: str

    def run(self, command: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                "-p",
                str(self.port),
                "-i",
                str(self.key_path),
                f"{self.user}@{self.host}",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )


SSH_IMAGE = "linuxserver/openssh-server:latest"
SSH_USER = "testuser"
SSH_INTERNAL_PORT = 2222
STARTUP_TIMEOUT = 120


def _generate_keypair(directory: Path) -> Path:
    key_path = directory / "id_ed25519"
    subprocess.run(
        [
            "ssh-keygen",
            "-t",
            "ed25519",
            "-f",
            str(key_path),
            "-N",
            "",
            "-q",
            "-C",
            "0sys-integration-test",
        ],
        check=True,
    )
    return key_path


def _read_public_key(key_path: Path) -> str:
    return key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()


def _wait_for_ssh(target: SshTarget, timeout: int = STARTUP_TIMEOUT) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        result = target.run("true", timeout=10)
        if result.returncode == 0:
            return
        last_error = result.stderr.strip() or f"exit code {result.returncode}"
        time.sleep(2)
    raise TimeoutError(f"SSH did not become available: {last_error}")


@pytest.fixture(scope="session")
def ssh_target(tmp_path_factory: pytest.TempPathFactory) -> Iterator[SshTarget]:
    if not _DOCKER_AVAILABLE:
        pytest.skip("docker SDK not available")

    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            check=True,
            timeout=10,
        )
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as exc:
        pytest.skip(f"docker daemon not available: {exc}")

    key_dir = tmp_path_factory.mktemp("ssh_keys")
    key_path = _generate_keypair(key_dir)
    public_key = _read_public_key(key_path)

    container = DockerContainer(SSH_IMAGE)
    container.with_env("PUID", "1000")
    container.with_env("PGID", "1000")
    container.with_env("TZ", "UTC")
    container.with_env("USER_NAME", SSH_USER)
    container.with_env("PUBLIC_KEY", public_key)
    container.with_env("SUDO_ACCESS", "true")
    container.with_env("PASSWORD_ACCESS", "false")
    container.with_exposed_ports(SSH_INTERNAL_PORT)

    container.start()

    try:
        container_id = container.get_wrapped_container().id
        host = container.get_container_host_ip()
        port = int(container.get_exposed_port(SSH_INTERNAL_PORT))

        target = SshTarget(
            host=host,
            port=port,
            user=SSH_USER,
            key_path=key_path,
            container_id=container_id,
        )

        _wait_for_ssh(target)

        yield target
    finally:
        container.stop()
