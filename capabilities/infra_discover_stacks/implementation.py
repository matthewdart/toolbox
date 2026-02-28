"""Core capability: scan /opt for deployable Docker Compose stacks."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from capabilities._infra_common import run_shell


class DiscoverStacksError(Exception):
    """Base error for discover-stacks failures."""


class DependencyError(DiscoverStacksError):
    """Raised when required external dependencies are missing."""


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
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Scan for deployable Docker Compose stacks.

    Looks for {base_dir}/*/docker-compose.yml and reports each stack's
    name, whether it has an override file, .env file, and running status.

    Raises:
        DiscoverStacksError: If the scan command fails.
    """
    script = _scan_script(base_dir)

    proc = run_shell(script)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "scan command failed"
        raise DiscoverStacksError(error_msg)

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
        "base_dir": base_dir,
        "stack_count": len(stacks),
        "stacks": stacks,
    }
