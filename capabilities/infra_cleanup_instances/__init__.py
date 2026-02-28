"""infra.cleanup_instances capability plugin."""
from __future__ import annotations

CAPABILITY_ID = "infra.cleanup_instances"
ENTRY_POINT_MODULE = "capabilities.infra_cleanup_instances.implementation"
ENTRY_POINT_ATTR = "cleanup_instances"
