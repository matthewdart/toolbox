"""Core capability: deploy a static stack locally via docker compose."""
from __future__ import annotations

import re
import shlex
from typing import Any, Dict, List, Optional

from capabilities._infra_common import run_shell


class DeployStackError(Exception):
    """Base error for deploy-stack failures."""


class DependencyError(DeployStackError):
    """Raised when required external dependencies are missing."""


def deploy_stack(
    *,
    stack: str,
    services: Optional[List[str]] = None,
    pull_only: bool = False,
    dry_run: bool = False,
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Deploy a static stack locally via docker compose pull && up -d.

    Resolves the stack to {base_dir}/{stack} and runs
    docker compose pull && docker compose up -d.

    Raises:
        DependencyError: If docker is not found in PATH.
        DeployStackError: If the command fails.
    """
    # Validate stack name — becomes a path component
    _SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not _SAFE_NAME.match(stack):
        raise DeployStackError(f"Invalid stack name: {stack!r}")

    compose_dir = f"{base_dir}/{stack}"
    effective_services = services or []
    svc_args = " ".join(shlex.quote(s) for s in effective_services)
    pull_cmd = f"docker compose pull {svc_args}".strip()

    if pull_only:
        shell_cmd = f"cd {shlex.quote(compose_dir)} && {pull_cmd}"
    else:
        up_cmd = f"docker compose up -d {svc_args}".strip()
        shell_cmd = f"cd {shlex.quote(compose_dir)} && {pull_cmd} && {up_cmd}"

    display_services = effective_services or ["(all)"]

    if dry_run:
        return {
            "stack": stack,
            "compose_dir": compose_dir,
            "services": display_services,
            "action": "dry_run",
            "command": shell_cmd,
        }

    proc = run_shell(shell_cmd)
    action = "pulled" if pull_only else "deployed"

    result: Dict[str, Any] = {
        "stack": stack,
        "compose_dir": compose_dir,
        "services": display_services,
        "action": action,
        "exit_code": proc.returncode,
    }

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "command failed"
        result["error"] = error_msg
        raise DeployStackError(error_msg)

    return result
