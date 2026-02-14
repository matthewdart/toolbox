"""Verify capability plugin structure and surface consistency."""
from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path

CAPABILITIES_DIR = Path(__file__).resolve().parents[1] / "capabilities"


class SurfaceConsistencyTests(unittest.TestCase):
    """Walk all capability plugins and verify structural consistency."""

    def _capability_dirs(self) -> list[Path]:
        return sorted(
            d for d in CAPABILITIES_DIR.iterdir()
            if d.is_dir() and (d / "contract.v1.json").is_file()
        )

    def test_all_capabilities_have_required_files(self) -> None:
        for cap_dir in self._capability_dirs():
            with self.subTest(capability=cap_dir.name):
                self.assertTrue(
                    (cap_dir / "__init__.py").is_file(),
                    f"{cap_dir.name}: missing __init__.py",
                )
                self.assertTrue(
                    (cap_dir / "implementation.py").is_file(),
                    f"{cap_dir.name}: missing implementation.py",
                )
                self.assertTrue(
                    (cap_dir / "contract.v1.json").is_file(),
                    f"{cap_dir.name}: missing contract.v1.json",
                )

    def test_contracts_are_valid_json(self) -> None:
        for cap_dir in self._capability_dirs():
            contract_path = cap_dir / "contract.v1.json"
            with self.subTest(capability=cap_dir.name):
                text = contract_path.read_text(encoding="utf-8")
                contract = json.loads(text)
                self.assertIn("name", contract, f"{cap_dir.name}: contract missing 'name'")
                self.assertIn("input_schema", contract, f"{cap_dir.name}: contract missing 'input_schema'")
                self.assertIn("output_schema", contract, f"{cap_dir.name}: contract missing 'output_schema'")

    def test_init_metadata_matches_contract(self) -> None:
        for cap_dir in self._capability_dirs():
            with self.subTest(capability=cap_dir.name):
                contract = json.loads((cap_dir / "contract.v1.json").read_text(encoding="utf-8"))
                module_name = f"capabilities.{cap_dir.name}"
                mod = importlib.import_module(module_name)
                capability_id = getattr(mod, "CAPABILITY_ID", None)
                self.assertEqual(
                    capability_id,
                    contract["name"],
                    f"{cap_dir.name}: CAPABILITY_ID '{capability_id}' != contract name '{contract['name']}'",
                )

    def test_entry_points_are_importable(self) -> None:
        for cap_dir in self._capability_dirs():
            with self.subTest(capability=cap_dir.name):
                module_name = f"capabilities.{cap_dir.name}"
                mod = importlib.import_module(module_name)
                ep_module = getattr(mod, "ENTRY_POINT_MODULE", None)
                ep_attr = getattr(mod, "ENTRY_POINT_ATTR", None)
                self.assertIsNotNone(ep_module, f"{cap_dir.name}: missing ENTRY_POINT_MODULE")
                self.assertIsNotNone(ep_attr, f"{cap_dir.name}: missing ENTRY_POINT_ATTR")
                impl_mod = importlib.import_module(ep_module)
                entry_fn = getattr(impl_mod, ep_attr, None)
                self.assertIsNotNone(
                    entry_fn,
                    f"{cap_dir.name}: {ep_module}.{ep_attr} not found",
                )
                self.assertTrue(callable(entry_fn), f"{cap_dir.name}: {ep_attr} is not callable")

    def test_openai_adapters_match_contracts(self) -> None:
        for cap_dir in self._capability_dirs():
            adapter_path = cap_dir / "adapters" / "openai.json"
            if not adapter_path.is_file():
                continue
            with self.subTest(capability=cap_dir.name):
                contract = json.loads((cap_dir / "contract.v1.json").read_text(encoding="utf-8"))
                adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    adapter.get("function", {}).get("name"),
                    contract["name"],
                    f"{cap_dir.name}: openai.json name doesn't match contract",
                )


if __name__ == "__main__":
    unittest.main()
