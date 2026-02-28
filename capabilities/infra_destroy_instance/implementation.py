"""Core capability: tear down a template instance by Compose project name."""
from __future__ import annotations

import re
import shlex
import shutil
from typing import Any, Dict

from capabilities._infra_common import run_shell


class DestroyInstanceError(Exception):
    """Base error for destroy-instance failures."""


class DependencyError(DestroyInstanceError):
    """Raised when required external dependencies are missing."""


class ComposeError(DestroyInstanceError):
    """Raised when docker compose fails."""


def destroy_instance(
    *,
    project: str,
    volumes: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Tear down a template instance by Compose project name.

    Runs docker compose -p <project> down.

    Raises:
        DependencyError: If required binaries are not found.
        ComposeError: If docker compose down fails.
    """
    # Validate project name — Docker Compose project names are [a-z0-9_-]
    _SAFE_PROJECT = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not _SAFE_PROJECT.match(project):
        raise DestroyInstanceError(f"Invalid project name: {project!r}")

    if not shutil.which("docker"):
        raise DependencyError("docker not found in PATH")

    down_flags = "-v" if volumes else ""
    docker_cmd = f"docker compose -p {shlex.quote(project)} down {down_flags}".strip()

    proc = run_shell(docker_cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "compose down failed"
        raise ComposeError(error_msg)

    return {
        "project": project,
        "action": "destroyed",
        "volumes_removed": volumes,
        "exit_code": proc.returncode,
        "hint": "Call gateway_reload to remove stale MCP services.",
    }
