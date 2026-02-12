"""Capability registry with auto-discovery from capabilities/ plugins."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

CAPABILITIES_DIR = Path(__file__).resolve().parents[1] / "capabilities"


def _discover() -> Tuple[Dict[str, Callable[..., Any]], Dict[str, Dict[str, Any]]]:
    """Scan capabilities/ for plugins and build the registry + contracts map.

    Each plugin directory must contain:
    - contract.v1.json with a 'name' field (the canonical capability ID)
    - __init__.py exporting ENTRY_POINT_MODULE and ENTRY_POINT_ATTR

    Imports are lazy: the implementation module is only loaded when the
    capability is first dispatched, not at discovery time. This allows
    capabilities with heavy dependencies (e.g. openai) to coexist with
    lightweight ones without requiring all deps to be installed.
    """
    registry: Dict[str, Callable[..., Any]] = {}
    contracts: Dict[str, Dict[str, Any]] = {}

    if not CAPABILITIES_DIR.is_dir():
        return registry, contracts

    for child in sorted(CAPABILITIES_DIR.iterdir()):
        if not child.is_dir():
            continue
        contract_path = child / "contract.v1.json"
        init_path = child / "__init__.py"
        if not contract_path.is_file() or not init_path.is_file():
            continue

        with contract_path.open("r", encoding="utf-8") as handle:
            contract = json.load(handle)
        capability_id = contract.get("name")
        if not capability_id:
            continue

        module_name = f"capabilities.{child.name}"
        try:
            mod = importlib.import_module(module_name)
        except Exception:
            continue

        ep_module = getattr(mod, "ENTRY_POINT_MODULE", None)
        ep_attr = getattr(mod, "ENTRY_POINT_ATTR", None)
        if not ep_module or not ep_attr:
            continue

        def _make_lazy(mod_name: str, attr_name: str) -> Callable[..., Any]:
            _resolved: list = []

            def _lazy_call(**kwargs: Any) -> Any:
                if not _resolved:
                    impl = importlib.import_module(mod_name)
                    _resolved.append(getattr(impl, attr_name))
                return _resolved[0](**kwargs)

            return _lazy_call

        registry[capability_id] = _make_lazy(ep_module, ep_attr)
        contracts[capability_id] = contract

    return registry, contracts


REGISTRY, CONTRACTS = _discover()
