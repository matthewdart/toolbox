"""Core capability: scan /opt for ephemeral Docker Compose templates."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from capabilities._infra_common import run_shell


class DiscoverTemplatesError(Exception):
    """Base error for discover-templates failures."""


class DependencyError(DiscoverTemplatesError):
    """Raised when required external dependencies are missing."""


def _extract_env_vars(content: str) -> List[str]:
    """Extract ${VAR} references from compose template content."""
    return sorted(set(re.findall(r'\$\{([A-Z_][A-Z0-9_]*?)(?::?-[^}]*)?\}', content)))


def discover_templates(
    *,
    base_dir: str = "/opt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Scan for ephemeral Docker Compose templates.

    Looks for {base_dir}/*/docker-compose.template.yml and reports each
    template's name, path, and required environment variables.

    Raises:
        DiscoverTemplatesError: If the scan command fails.
    """
    # Script to find templates and cat their contents
    script = f'''
cd {base_dir} 2>/dev/null || exit 1
for dir in */; do
    dir="${{dir%/}}"
    tmpl="$dir/docker-compose.template.yml"
    [ -f "$tmpl" ] || continue
    echo "===TEMPLATE:$dir==="
    cat "$tmpl"
done
'''

    proc = run_shell(script)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "command failed"
        raise DiscoverTemplatesError(error_msg)

    templates: List[Dict[str, Any]] = []
    current_name: Optional[str] = None
    current_content: list[str] = []

    for line in proc.stdout.splitlines():
        if line.startswith("===TEMPLATE:") and line.endswith("==="):
            # Save previous template
            if current_name is not None:
                content = "\n".join(current_content)
                templates.append({
                    "name": current_name,
                    "path": f"{base_dir}/{current_name}/docker-compose.template.yml",
                    "env_vars": _extract_env_vars(content),
                })
            current_name = line[len("===TEMPLATE:"):-len("===")]
            current_content = []
        else:
            current_content.append(line)

    # Save last template
    if current_name is not None:
        content = "\n".join(current_content)
        templates.append({
            "name": current_name,
            "path": f"{base_dir}/{current_name}/docker-compose.template.yml",
            "env_vars": _extract_env_vars(content),
        })

    return {
        "base_dir": base_dir,
        "template_count": len(templates),
        "templates": templates,
    }
