"""Generate OpenAI tool definitions from capability contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List

from core.registry import CONTRACTS

CAPABILITIES_DIR = Path(__file__).resolve().parents[2] / "capabilities"


def _strip_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(schema)
    cleaned.pop("$schema", None)
    return cleaned


def generate_tool(contract: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": contract["name"],
            "description": contract.get("description", ""),
            "parameters": _strip_schema(contract.get("input_schema", {})),
        },
    }


def _find_capability_dir(capability_id: str) -> Path | None:
    """Find the capability plugin directory for a given ID."""
    for child in sorted(CAPABILITIES_DIR.iterdir()):
        if not child.is_dir():
            continue
        contract_path = child / "contract.v1.json"
        if not contract_path.is_file():
            continue
        with contract_path.open("r", encoding="utf-8") as f:
            contract = json.load(f)
        if contract.get("name") == capability_id:
            return child
    return None


def write_tool(tool: Dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "openai.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(tool, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate OpenAI tool JSON files.")
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (default: write into each capability's adapters/ dir)",
    )
    args = parser.parse_args(argv)

    for capability_id, contract in sorted(CONTRACTS.items()):
        tool = generate_tool(contract)
        if args.out_dir:
            out = Path(args.out_dir)
            out.mkdir(parents=True, exist_ok=True)
            name = tool.get("function", {}).get("name", "unknown")
            output_path = out / f"{name}.json"
            with output_path.open("w", encoding="utf-8") as handle:
                json.dump(tool, handle, indent=2, sort_keys=True)
                handle.write("\n")
        else:
            cap_dir = _find_capability_dir(capability_id)
            if cap_dir:
                write_tool(tool, cap_dir / "adapters")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
