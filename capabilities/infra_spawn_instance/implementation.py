"""Core capability: create a named instance from a Docker Compose template."""
from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from typing import Any, Dict, Optional

SSH_BATCH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


class SpawnInstanceError(Exception):
    """Base error for spawn-instance failures."""


class DependencyError(SpawnInstanceError):
    """Raised when required external dependencies are missing."""


class SSHError(SpawnInstanceError):
    """Raised when the SSH connection or remote command fails."""


class ComposeError(SpawnInstanceError):
    """Raised when docker compose fails."""


def _run_local(cmd: list[str], env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """Execute a command locally."""
    import os
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, check=False, env=full_env,
    )


def _run_remote(host: str, remote_cmd: str) -> subprocess.CompletedProcess:
    """Execute a command on a remote host over SSH."""
    return subprocess.run(
        ["ssh", *SSH_BATCH_OPTIONS, host, remote_cmd],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )


def spawn_instance(
    *,
    template: str,
    name: str,
    host: str = "local",
    env: Optional[Dict[str, str]] = None,
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create a named instance from a Docker Compose template.

    Resolves the template to {base_dir}/{template}/docker-compose.template.yml,
    sets the project name to {template}-{name}, and runs docker compose up -d.

    Raises:
        DependencyError: If required binaries are not found.
        SSHError: If the SSH connection fails.
        ComposeError: If docker compose fails.
    """
    if host != "local" and not shutil.which("ssh"):
        raise DependencyError("ssh not found in PATH")

    # Validate template and name — these become paths and project names
    _SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not _SAFE_NAME.match(template):
        raise SpawnInstanceError(f"Invalid template name: {template!r}")
    if not _SAFE_NAME.match(name):
        raise SpawnInstanceError(f"Invalid instance name: {name!r}")

    template_path = f"{base_dir}/{template}/docker-compose.template.yml"
    project_name = f"{template}-{name}"

    # Build environment: NAME is always set, plus any caller-provided vars
    compose_env = {"NAME": name}
    if env:
        compose_env.update(env)

    if host == "local":
        if not shutil.which("docker"):
            raise DependencyError("docker not found in PATH")

        proc = _run_local(
            ["docker", "compose", "-f", template_path, "-p", project_name, "up", "-d"],
            env=compose_env,
        )
    else:
        # Shell-safe env exports for remote execution
        env_exports = " ".join(
            f"{k}={shlex.quote(v)}" for k, v in compose_env.items()
        )
        remote_cmd = (
            f"cd {shlex.quote(f'{base_dir}/{template}')} && "
            f"{env_exports} "
            f"docker compose -f docker-compose.template.yml -p {shlex.quote(project_name)} up -d"
        )
        proc = _run_remote(host, remote_cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or proc.stdout.strip() or "compose up failed"
        raise ComposeError(error_msg)

    result: Dict[str, Any] = {
        "host": host,
        "template": template,
        "name": name,
        "project_name": project_name,
        "action": "spawned",
        "exit_code": proc.returncode,
        "hint": "Call gateway_reload to make MCP tools available.",
    }

    return result
