"""Tests for the FastMCP MCP adapter."""
from __future__ import annotations

import asyncio
import unittest

from fastmcp import Client

from adapters.mcp.server import mcp
from core.registry import CONTRACTS


class FastMCPAdapterTests(unittest.TestCase):
    """Verify all capabilities are registered and callable via MCP."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_all_contracts_registered_as_tools(self):
        """Every contract should appear as an MCP tool (plus the meta-tool)."""

        async def check():
            async with Client(mcp) as client:
                tools = await client.list_tools()
                tool_names = {t.name for t in tools}
                for cap_id in CONTRACTS:
                    tool_name = cap_id.replace(".", "_")
                    self.assertIn(tool_name, tool_names, f"Missing tool for {cap_id}")
                self.assertIn("toolbox_list_capabilities", tool_names)

        self._run(check())

    def test_tool_schemas_match_contracts(self):
        """Each tool's inputSchema should match the contract's input_schema."""

        async def check():
            async with Client(mcp) as client:
                tools = await client.list_tools()
                tool_map = {t.name: t for t in tools}
                for cap_id, contract in CONTRACTS.items():
                    tool_name = cap_id.replace(".", "_")
                    tool = tool_map[tool_name]
                    expected_props = set(
                        contract.get("input_schema", {}).get("properties", {}).keys()
                    )
                    actual_props = set(
                        tool.inputSchema.get("properties", {}).keys()
                    )
                    self.assertEqual(
                        expected_props,
                        actual_props,
                        f"Schema mismatch for {cap_id}",
                    )

        self._run(check())

    def test_list_capabilities_returns_all(self):
        """The meta-tool should list every known capability."""

        async def check():
            async with Client(mcp) as client:
                result = await client.call_tool("toolbox_list_capabilities", {})
                # result.data is the dict returned by the tool
                cap_list = result.data["result"]
                self.assertEqual(sorted(cap_list), sorted(CONTRACTS.keys()))

        self._run(check())

    def test_call_normalize_markdown(self):
        """Calling a real (pure-Python) capability should work end-to-end."""

        async def check():
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "text_normalize_markdown", {"text": "hello"}
                )
                self.assertTrue(result.data["ok"])
                self.assertIn("text", result.data["result"])

        self._run(check())


if __name__ == "__main__":
    unittest.main()
