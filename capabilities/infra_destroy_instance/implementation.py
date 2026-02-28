"""Core capability: tear down a template instance by Compose project name."""
from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from typing import Any, Dict, Optional

SSH_BATCH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


class DestroyInstanceError(Exception):
    """Base error for destroy-instance failures."""


class DependencyError(DestroyInstanceError):
    """Raised when required external dependencies are missing."""


class SSHError(DestroyInstanceError):
    """Raised when the SSH connection or remote command fails."""


class ComposeError(DestroyInstanceError):
    """Raised when docker compose fails."""


def _run_local(cmd: list[str]) -> subprocess.CompletedProcess:
    """Execute a command locally."""
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )


def _run_remote(host: str, remote_cmd: str) -> subprocess.CompletedProcess:
    """Execute a command on a remote host over SSH."""
    return subprocess.run(
        ["ssh", *SSH_BATCH_OPTIONS, host, remote_cmd],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )


def destroy_instance(
    *,
    project: str,
    host: str = "local",
    volumes: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Tear down a template instance by Compose project name.

    Runs docker compose -p <project> down.

    Raises:
        DependencyError: If required binaries are not found.
        SSHError: If the SSH connection fails.
        ComposeError: If docker compose down fails.
    """
    if host != "local" and not shutil.which("ssh"):
        raise DependencyError("ssh not found in PATH")

    # Validate project name — Docker Compose project names are [a-z0-9_-]
    _SAFE_PROJECT = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not _SAFE_PROJECT.match(project):
        raise DestroyInstanceError(f"Invalid project name: {project!r}")

    down_flags = "-v" if volumes else ""
    docker_cmd = f"docker compose -p {shlex.quote(project)} down {down_flags}".strip()

    if host == "local":
        if not shutil.which("docker"):
            raise DependencyError("docker not found in PATH")
        proc = _run_local(["sh", "-c", docker_cmd])
    else:
        proc = _run_remote(host, docker_cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "compose down failed"
        raise ComposeError(error_msg)

    return {
        "host": host,
        "project": project,
        "action": "destroyed",
        "volumes_removed": volumes,
        "exit_code": proc.returncode,
        "hint": "Call gateway_reload to remove stale MCP services.",
    }
