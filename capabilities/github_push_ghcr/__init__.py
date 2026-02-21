"""github.push_ghcr capability plugin."""
from __future__ import annotations

CAPABILITY_ID = "github.push_ghcr"
ENTRY_POINT_MODULE = "capabilities.github_push_ghcr.implementation"
ENTRY_POINT_ATTR = "push_ghcr"
