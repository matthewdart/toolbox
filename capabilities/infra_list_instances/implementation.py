"""Core capability: list running template instances managed by toolbox."""
from __future__ import annotations

import json
import re
import shutil
from typing import Any, Dict, List, Optional

from capabilities._infra_common import run_cmd


class ListInstancesError(Exception):
    """Base error for list-instances failures."""


class DependencyError(ListInstancesError):
    """Raised when required external dependencies are missing."""


def _parse_containers(output: str) -> List[Dict[str, Any]]:
    """Parse docker ps --format json output into a list of dicts."""
    containers = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            containers.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return containers


def _group_by_project(containers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group containers by Compose project name."""
    projects: Dict[str, Dict[str, Any]] = {}
    for c in containers:
        labels = c.get("Labels", "")
        # Parse labels string (key=value,key=value format from docker ps)
        label_dict = {}
        if labels:
            for pair in labels.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    label_dict[k] = v

        project = label_dict.get("com.docker.compose.project", "unknown")
        template_type = label_dict.get("toolbox.type", "unknown")
        mcp_namespace = label_dict.get("mcp.namespace", "")

        if project not in projects:
            projects[project] = {
                "project_name": project,
                "type": template_type,
                "mcp_namespace": mcp_namespace,
                "containers": [],
            }

        projects[project]["containers"].append({
            "name": c.get("Names", "unknown"),
            "status": c.get("State", c.get("Status", "unknown")),
            "image": c.get("Image", "unknown"),
        })

        # Use first non-empty mcp_namespace
        if mcp_namespace and not projects[project]["mcp_namespace"]:
            projects[project]["mcp_namespace"] = mcp_namespace

    return list(projects.values())


def list_instances(
    *,
    template: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """List running template instances managed by toolbox.

    Filters containers by toolbox.managed=true label and optionally
    by toolbox.type={template}. Groups results by Compose project name.

    Raises:
        DependencyError: If required binaries are not found.
    """
    # Validate template filter if provided
    _SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")
    if template and not _SAFE_NAME.match(template):
        raise ListInstancesError(f"Invalid template filter: {template!r}")

    if not shutil.which("docker"):
        raise DependencyError("docker not found in PATH")

    cmd = ["docker", "ps", "--filter", "label=toolbox.managed=true"]
    if template:
        cmd.extend(["--filter", f"label=toolbox.type={template}"])
    cmd.extend(["--format", "json", "--no-trunc"])
    proc = run_cmd(cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "docker ps failed"
        raise ListInstancesError(error_msg)

    containers = _parse_containers(proc.stdout)
    instances = _group_by_project(containers)

    return {
        "filter_template": template,
        "instance_count": len(instances),
        "instances": instances,
    }
