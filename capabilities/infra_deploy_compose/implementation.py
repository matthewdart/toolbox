"""Core capability: deploy Docker Compose services on a remote host via SSH."""
from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional

SSH_BATCH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


class DeployComposeError(Exception):
    """Base error for deploy-compose failures."""


class DependencyError(DeployComposeError):
    """Raised when required external dependencies are missing."""


class SSHError(DeployComposeError):
    """Raised when the SSH connection or remote command fails."""


def _build_remote_command(compose_dir: str, services: List[str], pull_only: bool) -> str:
    """Build the shell command string to execute on the remote host."""
    svc_args = " ".join(services)
    pull_cmd = f"docker compose pull {svc_args}".strip()
    if pull_only:
        return f"cd {compose_dir} && {pull_cmd}"
    up_cmd = f"docker compose up -d {svc_args}".strip()
    return f"cd {compose_dir} && {pull_cmd} && {up_cmd}"


def _run_ssh(host: str, remote_cmd: str) -> subprocess.CompletedProcess:
    """Execute a command on the remote host over SSH."""
    return subprocess.run(
        ["ssh", *SSH_BATCH_OPTIONS, host, remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def deploy_compose(
    host: str,
    compose_dir: str,
    services: Optional[List[str]] = None,
    pull_only: bool = False,
    dry_run: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Deploy Docker Compose services on a remote host via SSH.

    Returns a dict describing the action taken and its outcome.
    Raises DependencyError if ssh is not available.
    Raises SSHError if the remote command fails with a non-zero exit code.
    """
    if not shutil.which("ssh"):
        raise DependencyError("ssh not found in PATH")

    effective_services = services or []
    remote_cmd = _build_remote_command(compose_dir, effective_services, pull_only)
    ssh_cmd = ["ssh", *SSH_BATCH_OPTIONS, host, remote_cmd]
    display_services = effective_services or ["(all)"]

    if dry_run:
        return {
            "host": host,
            "compose_dir": compose_dir,
            "services": display_services,
            "action": "dry_run",
            "ssh_command": ssh_cmd,
        }

    proc = _run_ssh(host, remote_cmd)
    action = "pulled" if pull_only else "deployed"

    result: Dict[str, Any] = {
        "host": host,
        "compose_dir": compose_dir,
        "services": display_services,
        "action": action,
        "exit_code": proc.returncode,
    }

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "remote command failed"
        result["error"] = error_msg
        raise SSHError(error_msg)

    return result
