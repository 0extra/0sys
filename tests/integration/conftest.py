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


IMAGE_TAG = "0sys-integration-ssh:latest"
DOCKERFILE_PATH = Path(__file__).parent / "Dockerfile"
SSH_USER = "testuser"
SSH_INTERNAL_PORT = 22
STARTUP_TIMEOUT = 120

UNEXPECTED_PACKAGES = ("curl", "ufw")


def _docker_available() -> bool:
    if not _DOCKER_AVAILABLE:
        return False
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
    ):
        return False
    return True


def _ensure_image() -> None:
    existing = subprocess.run(
        ["docker", "images", "-q", IMAGE_TAG],
        capture_output=True,
        text=True,
        check=False,
    )
    if existing.returncode == 0 and existing.stdout.strip():
        return
    subprocess.run(
        [
            "docker",
            "build",
            "-t",
            IMAGE_TAG,
            "-f",
            str(DOCKERFILE_PATH),
            str(DOCKERFILE_PATH.parent),
        ],
        check=True,
    )


def _verify_container_clean(container_id: str) -> None:
    check_script = (
        "for pkg in " + " ".join(UNEXPECTED_PACKAGES) + "; do "
        '  if command -v "$pkg" >/dev/null 2>&1; then echo "$pkg"; fi; '
        "done"
    )
    result = subprocess.run(
        ["docker", "exec", container_id, "sh", "-c", check_script],
        capture_output=True,
        text=True,
        check=False,
    )
    found = result.stdout.strip()
    if found:
        raise RuntimeError(
            f"Integration container has pre-installed packages: {found}. "
            "This breaks idempotency assertions. "
            "Rebuild the image with 'docker rmi " + IMAGE_TAG + "' and rerun."
        )


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


@pytest.fixture(scope="module")
def ssh_target(tmp_path_factory: pytest.TempPathFactory) -> Iterator[SshTarget]:
    if not _docker_available():
        pytest.skip("docker daemon not available")

    _ensure_image()

    key_dir = tmp_path_factory.mktemp("ssh_keys")
    key_path = _generate_keypair(key_dir)
    public_key = _read_public_key(key_path)

    container = DockerContainer(IMAGE_TAG)
    container.with_exposed_ports(SSH_INTERNAL_PORT)
    container.with_kwargs(cap_add=["NET_ADMIN", "NET_RAW"])

    container.start()

    try:
        container_id = container.get_wrapped_container().id
        host = container.get_container_host_ip()
        port = int(container.get_exposed_port(SSH_INTERNAL_PORT))

        _verify_container_clean(container_id)

        subprocess.run(
            [
                "docker",
                "exec",
                container_id,
                "sh",
                "-c",
                f"mkdir -p /home/{SSH_USER}/.ssh && "
                f"echo '{public_key}' > /home/{SSH_USER}/.ssh/authorized_keys && "
                f"chmod 700 /home/{SSH_USER}/.ssh && "
                f"chmod 600 /home/{SSH_USER}/.ssh/authorized_keys && "
                f"chown -R {SSH_USER}:{SSH_USER} /home/{SSH_USER}/.ssh",
            ],
            check=True,
        )

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
