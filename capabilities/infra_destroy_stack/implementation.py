"""Core capability: tear down a static stack locally via docker compose."""
from __future__ import annotations

import re
import shlex
from typing import Any, Dict

from capabilities._infra_common import run_shell


class DestroyStackError(Exception):
    """Base error for destroy-stack failures."""


class DependencyError(DestroyStackError):
    """Raised when required external dependencies are missing."""


def destroy_stack(
    *,
    stack: str,
    volumes: bool = False,
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Tear down a static stack locally.

    Resolves the stack to {base_dir}/{stack} and runs docker compose down.

    Raises:
        DependencyError: If docker is not found in PATH.
        DestroyStackError: If the command fails.
    """
    # Validate stack name — becomes a path component
    _SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not _SAFE_NAME.match(stack):
        raise DestroyStackError(f"Invalid stack name: {stack!r}")

    compose_dir = f"{base_dir}/{stack}"
    down_flags = "-v" if volumes else ""
    shell_cmd = f"cd {shlex.quote(compose_dir)} && docker compose down {down_flags}".strip()

    proc = run_shell(shell_cmd)

    result: Dict[str, Any] = {
        "stack": stack,
        "compose_dir": compose_dir,
        "action": "destroyed",
        "volumes_removed": volumes,
        "exit_code": proc.returncode,
    }

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "command failed"
        result["error"] = error_msg
        raise DestroyStackError(error_msg)

    return result
