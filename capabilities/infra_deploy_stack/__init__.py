"""infra.deploy_stack capability plugin."""
from __future__ import annotations

CAPABILITY_ID = "infra.deploy_stack"
ENTRY_POINT_MODULE = "capabilities.infra_deploy_stack.implementation"
ENTRY_POINT_ATTR = "deploy_stack"
