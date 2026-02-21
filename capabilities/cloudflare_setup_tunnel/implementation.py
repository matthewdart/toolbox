"""Core capability: generate Cloudflare Tunnel sidecar configuration for a Docker Compose service."""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional


_COMPOSE_TEMPLATE_SERVICE = dedent("""\
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: {service}-tunnel
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${{CF_TUNNEL_TOKEN}}
    network_mode: "service:{service}"
    depends_on:
      - {service}
""")

_COMPOSE_TEMPLATE_HOST = dedent("""\
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: {service}-tunnel
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${{CF_TUNNEL_TOKEN}}
    network_mode: host
    depends_on:
      - {service}
""")

_ENV_TEMPLATE = dedent("""\
# ---- Cloudflare Tunnel ----
# Dedicated tunnel token for this service.
# Create in: Cloudflare Zero Trust > Networks > Tunnels > Create
# Configure public hostname to route to http://localhost:{port}
CF_TUNNEL_TOKEN=
""")

_DASHBOARD_INSTRUCTIONS = dedent("""\
Dashboard setup steps:

  1. Go to Cloudflare Zero Trust > Networks > Tunnels
  2. Create a tunnel named: {service}
  3. Copy the tunnel token
  4. Paste it into .env as CF_TUNNEL_TOKEN=<token>
  5. In the tunnel config, add a public hostname:
     - Subdomain: {subdomain}
     - Domain: {domain}
     - Service: http://localhost:{port}
  6. Save and verify the tunnel shows as Connected

Networking strategy: {network_mode}
{network_note}
""")


def _split_hostname(hostname: str) -> tuple[str, str]:
    """Split a hostname into (subdomain, domain).

    Raises ValueError if the hostname is not in subdomain.domain format.
    """
    parts = hostname.split(".", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"hostname must be in subdomain.domain format (got: {hostname!r})"
        )
    return parts[0], parts[1]


def setup_tunnel(
    service: str,
    port: int,
    hostname: str,
    network_mode: str = "service",
    output_dir: Optional[str] = None,
    dry_run: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Generate Cloudflare Tunnel sidecar configuration for a Docker Compose service.

    Returns a dict with the generated compose block, env block, dashboard
    instructions, and a list of any files written to disk.

    Raises ValueError if hostname is not in subdomain.domain format.
    """
    subdomain, domain = _split_hostname(hostname)

    if network_mode == "service":
        compose_block = _COMPOSE_TEMPLATE_SERVICE.format(service=service)
        network_note = (
            f"  cloudflared shares {service}'s network namespace.\n"
            f"  The app can bind to localhost:{port}."
        )
    else:
        compose_block = _COMPOSE_TEMPLATE_HOST.format(service=service)
        network_note = (
            f"  Both {service} and cloudflared use host networking.\n"
            "  Use this when the app needs host-level resources (e.g. Tailscale)."
        )

    env_block = _ENV_TEMPLATE.format(port=port)

    instructions = _DASHBOARD_INSTRUCTIONS.format(
        service=service,
        subdomain=subdomain,
        domain=domain,
        port=port,
        network_mode=network_mode,
        network_note=network_note,
    )

    generated_files: List[str] = []

    if output_dir and not dry_run:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        compose_path = out / "cloudflared-compose-block.yml"
        compose_path.write_text(compose_block)
        generated_files.append(str(compose_path))

        env_path = out / "cloudflared-env-block.txt"
        env_path.write_text(env_block)
        generated_files.append(str(env_path))

    return {
        "service": service,
        "port": port,
        "hostname": hostname,
        "network_mode": network_mode,
        "compose_block": compose_block,
        "env_block": env_block,
        "instructions": instructions,
        "generated_files": generated_files,
    }
