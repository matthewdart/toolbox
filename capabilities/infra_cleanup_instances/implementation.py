"""Core capability: remove stopped/orphaned managed containers."""
from __future__ import annotations

import shutil
from typing import Any, Dict, List

from capabilities._infra_common import run_shell


class CleanupInstancesError(Exception):
    """Base error for cleanup-instances failures."""


class DependencyError(CleanupInstancesError):
    """Raised when required external dependencies are missing."""


def cleanup_instances(
    *,
    dry_run: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Remove stopped/orphaned managed containers.

    Finds containers with toolbox.managed=true label that are in
    exited or dead state, and removes them (or lists them if dry_run).

    Raises:
        DependencyError: If required binaries are not found.
    """
    if not shutil.which("docker"):
        raise DependencyError("docker not found in PATH")

    # Find stopped managed containers
    find_cmd = (
        'docker ps -a '
        '--filter "label=toolbox.managed=true" '
        '--filter "status=exited" '
        '--filter "status=dead" '
        '--format "{{.ID}} {{.Names}} {{.Image}} {{.Status}}"'
    )

    proc = run_shell(find_cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "docker ps failed"
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
            "action": "dry_run" if dry_run else "none",
            "count": len(candidates),
            "containers": candidates,
        }

    # Remove each container
    ids = " ".join(c["id"] for c in candidates)
    rm_cmd = f"docker rm {ids}"

    proc = run_shell(rm_cmd)

    removed = candidates if proc.returncode == 0 else []

    return {
        "action": "cleaned",
        "count": len(removed),
        "containers": removed,
        "exit_code": proc.returncode,
    }
