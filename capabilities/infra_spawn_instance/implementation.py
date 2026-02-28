"""Core capability: create a named instance from a Docker Compose template."""
from __future__ import annotations

import re
import shutil
from typing import Any, Dict, Optional

from capabilities._infra_common import run_cmd


class SpawnInstanceError(Exception):
    """Base error for spawn-instance failures."""


class DependencyError(SpawnInstanceError):
    """Raised when required external dependencies are missing."""


class ComposeError(SpawnInstanceError):
    """Raised when docker compose fails."""


def spawn_instance(
    *,
    template: str,
    name: str,
    env: Optional[Dict[str, str]] = None,
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create a named instance from a Docker Compose template.

    Resolves the template to {base_dir}/{template}/docker-compose.template.yml,
    sets the project name to {template}-{name}, and runs docker compose up -d.

    Raises:
        DependencyError: If required binaries are not found.
        ComposeError: If docker compose fails.
    """
    # Validate template and name — these become paths and project names
    _SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not _SAFE_NAME.match(template):
        raise SpawnInstanceError(f"Invalid template name: {template!r}")
    if not _SAFE_NAME.match(name):
        raise SpawnInstanceError(f"Invalid instance name: {name!r}")

    if not shutil.which("docker"):
        raise DependencyError("docker not found in PATH")

    template_path = f"{base_dir}/{template}/docker-compose.template.yml"
    project_name = f"{template}-{name}"

    # Build environment: NAME is always set, plus any caller-provided vars
    compose_env = {"NAME": name}
    if env:
        compose_env.update(env)

    proc = run_cmd(
        ["docker", "compose", "-f", template_path, "-p", project_name, "up", "-d"],
        env=compose_env,
    )

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or proc.stdout.strip() or "compose up failed"
        raise ComposeError(error_msg)

    result: Dict[str, Any] = {
        "template": template,
        "name": name,
        "project_name": project_name,
        "action": "spawned",
        "exit_code": proc.returncode,
        "hint": "Call gateway_reload to make MCP tools available.",
    }

    return result
