"""infra.ghcr_push capability plugin."""
from __future__ import annotations

CAPABILITY_ID = "infra.ghcr_push"
ENTRY_POINT_MODULE = "capabilities.ghcr_push.implementation"
ENTRY_POINT_ATTR = "ghcr_push"
