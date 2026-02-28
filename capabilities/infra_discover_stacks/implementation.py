"""Core capability: scan /opt for deployable Docker Compose stacks."""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Dict, List, Optional

SSH_BATCH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


class DiscoverStacksError(Exception):
    """Base error for discover-stacks failures."""


class DependencyError(DiscoverStacksError):
    """Raised when required external dependencies are missing."""


class SSHError(DiscoverStacksError):
    """Raised when the SSH connection or remote command fails."""


def _run_local(cmd: list[str]) -> subprocess.CompletedProcess:
    """Execute a command locally."""
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )


def _run_ssh(host: str, remote_cmd: str) -> subprocess.CompletedProcess:
    """Execute a command on the remote host over SSH."""
    return subprocess.run(
        ["ssh", *SSH_BATCH_OPTIONS, host, remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _scan_script(base_dir: str) -> str:
    """Shell script that scans for docker-compose stacks."""
    return f'''
cd {base_dir} 2>/dev/null || exit 1
for dir in */; do
    dir="${{dir%/}}"
    [ -f "$dir/docker-compose.yml" ] || continue
    has_override="false"
    [ -f "$dir/docker-compose.override.yml" ] && has_override="true"
    has_env="false"
    [ -f "$dir/.env" ] && has_env="true"
    has_template="false"
    [ -f "$dir/docker-compose.template.yml" ] && has_template="true"
    running=$(cd "$dir" && docker compose ps --format json 2>/dev/null | head -1)
    if [ -n "$running" ]; then
        status="running"
    else
        status="stopped"
    fi
    printf '%s\\n' "{{\\"name\\":\\"$dir\\",\\"has_override\\":$has_override,\\"has_env\\":$has_env,\\"has_template\\":$has_template,\\"status\\":\\"$status\\"}}"
done
'''


def discover_stacks(
    *,
    host: str = "local",
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Scan for deployable Docker Compose stacks.

    Looks for {base_dir}/*/docker-compose.yml and reports each stack's
    name, whether it has an override file, .env file, and running status.

    Raises:
        DependencyError: If required binaries are not found.
        SSHError: If the SSH connection fails.
    """
    script = _scan_script(base_dir)

    if host == "local":
        proc = _run_local(["sh", "-c", script])
    else:
        if not shutil.which("ssh"):
            raise DependencyError("ssh not found in PATH")
        proc = _run_ssh(host, script)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "remote command failed"
        raise SSHError(error_msg)

    stacks: List[Dict[str, Any]] = []
    for line in proc.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            stacks.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return {
        "host": host,
        "base_dir": base_dir,
        "stack_count": len(stacks),
        "stacks": stacks,
    }
