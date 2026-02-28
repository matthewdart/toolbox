"""Core capability: deploy a static stack to a host via SSH."""
from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from typing import Any, Dict, List, Optional

SSH_BATCH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


class DeployStackError(Exception):
    """Base error for deploy-stack failures."""


class DependencyError(DeployStackError):
    """Raised when required external dependencies are missing."""


class SSHError(DeployStackError):
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


def deploy_stack(
    *,
    host: str,
    stack: str,
    services: Optional[List[str]] = None,
    pull_only: bool = False,
    dry_run: bool = False,
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Deploy a static stack to a host via SSH.

    Resolves the stack to {base_dir}/{stack} and runs
    docker compose pull && docker compose up -d.

    Raises:
        DependencyError: If ssh is not found in PATH.
        SSHError: If the remote command fails.
    """
    if not shutil.which("ssh"):
        raise DependencyError("ssh not found in PATH")

    # Validate stack name — becomes a path component
    _SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not _SAFE_NAME.match(stack):
        raise DeployStackError(f"Invalid stack name: {stack!r}")

    compose_dir = f"{base_dir}/{stack}"
    effective_services = services or []
    svc_args = " ".join(shlex.quote(s) for s in effective_services)
    pull_cmd = f"docker compose pull {svc_args}".strip()

    if pull_only:
        remote_cmd = f"cd {shlex.quote(compose_dir)} && {pull_cmd}"
    else:
        up_cmd = f"docker compose up -d {svc_args}".strip()
        remote_cmd = f"cd {shlex.quote(compose_dir)} && {pull_cmd} && {up_cmd}"

    ssh_cmd = ["ssh", *SSH_BATCH_OPTIONS, host, remote_cmd]
    display_services = effective_services or ["(all)"]

    if dry_run:
        return {
            "host": host,
            "stack": stack,
            "compose_dir": compose_dir,
            "services": display_services,
            "action": "dry_run",
            "ssh_command": ssh_cmd,
        }

    proc = _run_ssh(host, remote_cmd)
    action = "pulled" if pull_only else "deployed"

    result: Dict[str, Any] = {
        "host": host,
        "stack": stack,
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
