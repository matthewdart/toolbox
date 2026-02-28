"""infra.destroy_instance capability plugin."""
from __future__ import annotations

CAPABILITY_ID = "infra.destroy_instance"
ENTRY_POINT_MODULE = "capabilities.infra_destroy_instance.implementation"
ENTRY_POINT_ATTR = "destroy_instance"
