"""infra.destroy_stack capability plugin."""
from __future__ import annotations

CAPABILITY_ID = "infra.destroy_stack"
ENTRY_POINT_MODULE = "capabilities.infra_destroy_stack.implementation"
ENTRY_POINT_ATTR = "destroy_stack"
