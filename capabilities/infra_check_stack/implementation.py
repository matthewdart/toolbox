"""Core capability: check Docker Compose service status locally."""
from __future__ import annotations

import json
import shutil
from typing import Any, Dict, List, Optional

from capabilities._infra_common import run_shell


class StackStatusError(Exception):
    """Base error for stack status failures."""


class DependencyError(StackStatusError):
    """Raised when required external dependencies are missing."""


def _parse_compose_ps(raw_output: str) -> List[Dict[str, Any]]:
    """Parse docker compose ps --format json output.

    Docker Compose may emit one JSON object per line (not a JSON array),
    so both formats are handled.
    """
    services: List[Dict[str, Any]] = []
    if not raw_output.strip():
        return services
    try:
        data = json.loads(raw_output)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass
    for line in raw_output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            services.append(obj)
        except json.JSONDecodeError:
            continue
    return services


def _normalize_service(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize docker compose ps JSON to a consistent schema."""
    return {
        "name": svc.get("Name") or svc.get("Service") or svc.get("name", "unknown"),
        "service": svc.get("Service") or svc.get("service", ""),
        "status": svc.get("State") or svc.get("Status") or svc.get("status", "unknown"),
        "health": svc.get("Health") or svc.get("health", ""),
        "ports": svc.get("Publishers") or svc.get("Ports") or svc.get("ports", ""),
        "image": svc.get("Image") or svc.get("image", ""),
    }


def check_stack(
    *,
    compose_dir: str,
    services: Optional[List[str]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Check Docker Compose service status locally.

    Args:
        compose_dir: Absolute path to the Docker Compose project directory.
        services: Optional list of service names to query. If None or empty,
            all services are returned.

    Returns:
        A dict containing compose_dir, service_count, and services list.
        On command failure, returns compose_dir, error, and exit_code.

    Raises:
        DependencyError: If docker is not found in PATH.
    """
    if not shutil.which("docker"):
        raise DependencyError("docker not found in PATH")

    svc_args = " ".join(services) if services else ""
    shell_cmd = f"cd {compose_dir} && docker compose ps --format json {svc_args}".strip()

    proc = run_shell(shell_cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "command failed"
        return {
            "compose_dir": compose_dir,
            "error": error_msg,
            "exit_code": proc.returncode,
        }

    raw_services = _parse_compose_ps(proc.stdout)
    normalized = [_normalize_service(s) for s in raw_services]

    return {
        "compose_dir": compose_dir,
        "service_count": len(normalized),
        "services": normalized,
    }
