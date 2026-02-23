"""MCP server for toolbox capabilities — FastMCP 3.x adapter.

Replaces the raw mcp-sdk adapter with FastMCP, gaining:
- HTTP + stdio transport via env var
- Compatibility with mcp-gateway's Docker label discovery

Contracts remain the single source of truth. Each capability is registered
as a FunctionTool with its contract's input_schema passed explicitly as
`parameters`, bypassing FastMCP's function-signature introspection.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from core.dispatch import dispatch
from core.registry import CONTRACTS

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "toolbox",
    instructions=(
        "Toolbox exposes operational capabilities for infrastructure management, "
        "media processing, and developer workflows. Each tool corresponds to a "
        "capability with validated inputs and outputs."
    ),
)


def _strip_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Remove $schema key — FastMCP doesn't expect it in parameters."""
    cleaned = dict(schema)
    cleaned.pop("$schema", None)
    return cleaned


def _register_capability(capability_id: str, contract: Dict[str, Any]) -> None:
    """Register a single capability as a FastMCP tool.

    Constructs a FunctionTool directly with the contract's input_schema as
    explicit `parameters`. This bypasses FastMCP's function-signature
    introspection (which rejects **kwargs) while preserving the full JSON
    Schema for the LLM.
    """
    description = contract.get("description", "")
    input_schema = _strip_schema(contract.get("input_schema", {}))

    def make_handler(cap_id: str):
        def handler(**kwargs: Any) -> dict:
            return dispatch(cap_id, kwargs)
        return handler

    tool = FunctionTool(
        name=capability_id,
        description=description,
        fn=make_handler(capability_id),
        parameters=input_schema,
    )
    mcp.add_tool(tool)


# --- Register all discovered capabilities ---
for _cap_id, _contract in sorted(CONTRACTS.items()):
    try:
        _register_capability(_cap_id, _contract)
        logger.debug("Registered tool: %s", _cap_id)
    except Exception as e:
        logger.warning("Failed to register %s: %s", _cap_id, e)


# --- Meta-tool: list capabilities ---
@mcp.tool
def toolbox_list_capabilities() -> dict:
    """List all capability IDs available in this server."""
    return {"ok": True, "result": sorted(CONTRACTS.keys())}


def main() -> None:
    transport = os.environ.get("TOOLBOX_TRANSPORT", "stdio")
    host = os.environ.get("TOOLBOX_HOST", "127.0.0.1")
    port = int(os.environ.get("TOOLBOX_PORT", "8768"))

    if transport == "http":
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
