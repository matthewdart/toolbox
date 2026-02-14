"""infra.deploy_compose capability plugin."""
from __future__ import annotations

CAPABILITY_ID = "infra.deploy_compose"
ENTRY_POINT_MODULE = "capabilities.deploy_compose.implementation"
ENTRY_POINT_ATTR = "deploy_compose"
