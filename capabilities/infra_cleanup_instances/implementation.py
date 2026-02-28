"""Core capability: remove stopped/orphaned managed containers."""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Dict, List, Optional

SSH_BATCH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


class CleanupInstancesError(Exception):
    """Base error for cleanup-instances failures."""


class DependencyError(CleanupInstancesError):
    """Raised when required external dependencies are missing."""


class SSHError(CleanupInstancesError):
    """Raised when the SSH connection or remote command fails."""


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


def cleanup_instances(
    *,
    host: str = "local",
    dry_run: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Remove stopped/orphaned managed containers.

    Finds containers with toolbox.managed=true label that are in
    exited or dead state, and removes them (or lists them if dry_run).

    Raises:
        DependencyError: If required binaries are not found.
        SSHError: If the SSH connection fails.
    """
    if host != "local" and not shutil.which("ssh"):
        raise DependencyError("ssh not found in PATH")

    # Find stopped managed containers
    find_cmd = (
        'docker ps -a '
        '--filter "label=toolbox.managed=true" '
        '--filter "status=exited" '
        '--filter "status=dead" '
        '--format "{{.ID}} {{.Names}} {{.Image}} {{.Status}}"'
    )

    if host == "local":
        if not shutil.which("docker"):
            raise DependencyError("docker not found in PATH")
        proc = _run_local(["sh", "-c", find_cmd])
    else:
        proc = _run_remote(host, find_cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "docker ps failed"
        if host != "local":
            raise SSHError(error_msg)
        raise CleanupInstancesError(error_msg)

    candidates: List[Dict[str, str]] = []
    for line in proc.stdout.strip().splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) >= 2:
            candidates.append({
                "id": parts[0],
                "name": parts[1],
                "image": parts[2] if len(parts) > 2 else "unknown",
                "status": parts[3] if len(parts) > 3 else "unknown",
            })

    if dry_run or not candidates:
        return {
            "host": host,
            "action": "dry_run" if dry_run else "none",
            "count": len(candidates),
            "containers": candidates,
        }

    # Remove each container
    ids = " ".join(c["id"] for c in candidates)
    rm_cmd = f"docker rm {ids}"

    if host == "local":
        proc = _run_local(["sh", "-c", rm_cmd])
    else:
        proc = _run_remote(host, rm_cmd)

    removed = candidates if proc.returncode == 0 else []

    return {
        "host": host,
        "action": "cleaned",
        "count": len(removed),
        "containers": removed,
        "exit_code": proc.returncode,
    }
