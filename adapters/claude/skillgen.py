"""Generate Claude Code SKILL.md stubs from capability contracts.

Parallel to adapters/openai/toolgen.py — reads contracts from the registry
and writes SKILL.md files into .claude/skills/<slug>/.

By default, skips capabilities that already have a SKILL.md (handwritten or
otherwise). Use --force to overwrite.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from core.registry import CONTRACTS

SKILLS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "skills"


def _slug_from_id(capability_id: str) -> str:
    """Derive a kebab-case skill slug from a capability ID.

    infra.fleet_health     -> fleet-health
    session.survey_sessions -> survey-sessions

    Default: strip domain prefix, replace underscores with hyphens.
    """
    _, _, action = capability_id.partition(".")
    if not action:
        action = capability_id
    return action.replace("_", "-")


def _existing_skill_covers(capability_id: str, skills_dir: Path) -> str | None:
    """Check if any existing SKILL.md wraps/invokes this capability.

    Looks for patterns like '`gist.create_private` capability' that indicate
    the skill is specifically about this capability — not just a passing mention
    (e.g. keychain-secrets listing capabilities in a "Used by" table).

    Returns the skill slug if found, None otherwise.
    """
    if not skills_dir.is_dir():
        return None
    # Patterns that indicate the skill covers this capability
    markers = [
        f"`{capability_id}` capability",
        f"Call the `{capability_id}`",
        f"`{capability_id}` via MCP",
    ]
    for skill_dir in sorted(skills_dir.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        content = skill_md.read_text(encoding="utf-8")
        if any(m in content for m in markers):
            return skill_dir.name
    return None


def _param_table(schema: Dict[str, Any]) -> str:
    """Build a markdown parameter table from a JSON Schema."""
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not props:
        return "_No parameters._"

    rows = []
    rows.append("| Parameter | Type | Required | Default | Description |")
    rows.append("|-----------|------|----------|---------|-------------|")

    for name, spec in props.items():
        ptype = spec.get("type", "any")
        if isinstance(ptype, list):
            ptype = " | ".join(t for t in ptype if t != "null")
            if "null" in spec["type"]:
                ptype += "?"
        req = "yes" if name in required else "no"
        default = spec.get("default")
        if default is None:
            default_str = "—"
        else:
            default_str = f"`{json.dumps(default)}`"
        desc = spec.get("description", "")
        # Collapse enum values into description
        if "enum" in spec:
            vals = ", ".join(f"`{v}`" for v in spec["enum"] if v is not None)
            desc = f"{desc} Values: {vals}." if desc else f"One of: {vals}."
        rows.append(f"| `{name}` | {ptype} | {req} | {default_str} | {desc} |")

    return "\n".join(rows)


def _error_table(errors: List[Dict[str, str]]) -> str:
    if not errors:
        return ""
    rows = ["| Code | Description |", "|------|-------------|"]
    for e in errors:
        rows.append(f"| `{e['code']}` | {e['description']} |")
    return "\n".join(rows)


def _example_call(capability_id: str, schema: Dict[str, Any]) -> str:
    """Build an example invocation showing key parameters."""
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    parts = []
    for name, spec in props.items():
        if name not in required:
            continue
        ptype = spec.get("type", "string")
        if isinstance(ptype, list):
            ptype = [t for t in ptype if t != "null"][0] if ptype else "string"
        if ptype == "string":
            parts.append(f'{name}="..."')
        elif ptype == "boolean":
            parts.append(f"{name}=true")
        elif ptype == "integer" or ptype == "number":
            parts.append(f"{name}=0")
        elif ptype == "array":
            parts.append(f'{name}=["..."]')
        else:
            parts.append(f'{name}=...')
    return f"{capability_id}({', '.join(parts)})"


def generate_skill(contract: Dict[str, Any]) -> str:
    """Generate SKILL.md content from a capability contract."""
    cap_id = contract["name"]
    desc = contract.get("description", "")
    slug = _slug_from_id(cap_id)
    input_schema = contract.get("input_schema", {})
    errors = contract.get("errors", [])
    side_effects = contract.get("side_effects", "")

    # Title: convert slug to title case
    title = slug.replace("-", " ").title()

    lines = []

    # Frontmatter
    lines.append("---")
    lines.append(f"name: {slug}")
    lines.append(f"description: {desc}")
    lines.append("---")
    lines.append("")

    # Header
    lines.append(f"# {title}")
    lines.append("")
    lines.append(desc)
    lines.append("")

    # Invocation
    lines.append("## Invocation")
    lines.append("")
    lines.append(f"Call the `{cap_id}` capability via MCP:")
    lines.append("")
    lines.append("```")
    lines.append(_example_call(cap_id, input_schema))
    lines.append("```")
    lines.append("")

    # Parameters
    lines.append("## Parameters")
    lines.append("")
    lines.append(_param_table(input_schema))
    lines.append("")

    # Errors
    if errors:
        lines.append("## Error Codes")
        lines.append("")
        lines.append(_error_table(errors))
        lines.append("")

    # Side effects
    if side_effects:
        lines.append("## Side Effects")
        lines.append("")
        lines.append(side_effects)
        lines.append("")

    return "\n".join(lines)


def write_skill(content: str, slug: str, output_dir: Path) -> Path:
    skill_dir = output_dir / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    output_path = skill_dir / "SKILL.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate Claude Code SKILL.md stubs from capability contracts."
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help=f"Output directory (default: {SKILLS_DIR})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing SKILL.md files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be generated without writing files",
    )
    parser.add_argument(
        "--capability",
        default=None,
        help="Generate for a single capability ID only",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir) if args.out_dir else SKILLS_DIR
    generated = 0
    skipped = 0

    for cap_id, contract in sorted(CONTRACTS.items()):
        if args.capability and cap_id != args.capability:
            continue

        slug = _slug_from_id(cap_id)
        skill_path = out_dir / slug / "SKILL.md"

        if skill_path.exists() and not args.force:
            print(f"  skip  {slug:<30s}  (exists, use --force to overwrite)")
            skipped += 1
            continue

        # Check if a differently-named skill already covers this capability
        covered_by = _existing_skill_covers(cap_id, out_dir)
        if covered_by and not args.force:
            print(f"  skip  {slug:<30s}  (covered by {covered_by})")
            skipped += 1
            continue

        content = generate_skill(contract)

        if args.dry_run:
            print(f"  would write  {skill_path}")
            print(f"  --- {slug} ---")
            print(content)
            print()
        else:
            path = write_skill(content, slug, out_dir)
            action = "overwrite" if skill_path.exists() else "create"
            print(f"  {action}  {path.relative_to(out_dir.parent.parent)}")

        generated += 1

    print(f"\n{generated} generated, {skipped} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
