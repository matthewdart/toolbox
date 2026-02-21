"""cloudflare.setup_tunnel capability plugin."""
from __future__ import annotations

CAPABILITY_ID = "cloudflare.setup_tunnel"
ENTRY_POINT_MODULE = "capabilities.cloudflare_setup_tunnel.implementation"
ENTRY_POINT_ATTR = "setup_tunnel"
