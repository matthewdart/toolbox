"""Core capability: tear down a static stack on a remote host via SSH."""
from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from typing import Any, Dict

SSH_BATCH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


class DestroyStackError(Exception):
    """Base error for destroy-stack failures."""


class DependencyError(DestroyStackError):
    """Raised when required external dependencies are missing."""


class SSHError(DestroyStackError):
    """Raised when the SSH connection or remote command fails."""


def _run_ssh(host: str, remote_cmd: str) -> subprocess.CompletedProcess:
    """Execute a command on the remote host over SSH."""
    return subprocess.run(
        ["ssh", *SSH_BATCH_OPTIONS, host, remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def destroy_stack(
    *,
    host: str,
    stack: str,
    volumes: bool = False,
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Tear down a static stack on a remote host.

    Resolves the stack to {base_dir}/{stack} and runs docker compose down.

    Raises:
        DependencyError: If ssh is not found in PATH.
        SSHError: If the remote command fails.
    """
    if not shutil.which("ssh"):
        raise DependencyError("ssh not found in PATH")

    # Validate stack name — becomes a path component
    _SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not _SAFE_NAME.match(stack):
        raise DestroyStackError(f"Invalid stack name: {stack!r}")

    compose_dir = f"{base_dir}/{stack}"
    down_flags = "-v" if volumes else ""
    remote_cmd = f"cd {shlex.quote(compose_dir)} && docker compose down {down_flags}".strip()

    proc = _run_ssh(host, remote_cmd)

    result: Dict[str, Any] = {
        "host": host,
        "stack": stack,
        "compose_dir": compose_dir,
        "action": "destroyed",
        "volumes_removed": volumes,
        "exit_code": proc.returncode,
    }

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "remote command failed"
        result["error"] = error_msg
        raise SSHError(error_msg)

    return result
