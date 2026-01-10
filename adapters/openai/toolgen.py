"""Generate OpenAI tool definitions from contracts."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"
OUTPUT_DIR = Path(__file__).resolve().parent


def _load_contracts() -> List[Dict[str, Any]]:
    contracts: List[Dict[str, Any]] = []
    for path in sorted(CONTRACTS_DIR.glob("*.v1.json")):
        with path.open("r", encoding="utf-8") as handle:
            contract = json.load(handle)
        contracts.append(contract)
    return contracts


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


def write_tool(tool: Dict[str, Any], output_dir: Path) -> Path:
    name = tool.get("function", {}).get("name", "unknown")
    output_path = output_dir / f"{name}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(tool, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate OpenAI tool JSON files.")
    parser.add_argument(
        "--out-dir",
        default=str(OUTPUT_DIR),
        help="Output directory for tool JSON files",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contracts = _load_contracts()
    for contract in contracts:
        tool = generate_tool(contract)
        write_tool(tool, output_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
