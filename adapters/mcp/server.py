"""MCP stdio server for toolbox capabilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import validators
from mcp.server import Server
from mcp.server.stdio import stdio_server

from core.dispatch import dispatch

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"


def _load_contracts() -> Dict[str, Dict[str, Any]]:
    contracts: Dict[str, Dict[str, Any]] = {}
    for path in sorted(CONTRACTS_DIR.glob("*.v1.json")):
        with path.open("r", encoding="utf-8") as handle:
            contract = json.load(handle)
        name = contract.get("name")
        if name:
            contracts[name] = contract
    return contracts


def _strip_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(schema)
    cleaned.pop("$schema", None)
    return cleaned


def _validate(schema: Dict[str, Any], payload: Any) -> List[Dict[str, Any]]:
    validator_cls = validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    return [
        {"message": err.message, "path": list(err.path), "schema_path": list(err.schema_path)}
        for err in errors
    ]


contracts = _load_contracts()
server = Server("toolbox")


@server.list_tools()
async def list_tools() -> List[Dict[str, Any]]:
    tools = []
    for name, contract in contracts.items():
        tools.append(
            {
                "name": name,
                "description": contract.get("description", ""),
                "inputSchema": _strip_schema(contract.get("input_schema", {})),
            }
        )
    tools.append(
        {
            "name": "toolbox.list_capabilities",
            "description": "List capability ids available in this server.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        }
    )
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    if name == "toolbox.list_capabilities":
        return {"ok": True, "result": sorted(contracts.keys())}

    contract = contracts.get(name)
    if not contract:
        return {
            "ok": False,
            "error": {
                "type": "capability_not_found",
                "message": f"unknown capability: {name}",
            },
        }

    input_schema = contract.get("input_schema", {})
    errors = _validate(input_schema, arguments)
    if errors:
        return {
            "ok": False,
            "error": {
                "type": "validation_error",
                "message": "schema validation failed",
                "details": errors,
            },
        }

    return dispatch(name, arguments)


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


def main() -> int:
    import asyncio

    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
