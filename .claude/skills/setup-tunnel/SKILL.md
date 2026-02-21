---
name: setup-tunnel
description: Generate Cloudflare Tunnel sidecar configuration for a Docker Compose service. Produces a cloudflared compose service block, .env template, and dashboard setup instructions.
---

# Setup Tunnel

Generate Cloudflare Tunnel sidecar configuration for a Docker Compose service. Produces a cloudflared compose service block, .env template, and dashboard setup instructions.

## Invocation

Call the `cloudflare.setup_tunnel` capability via MCP:

```
cloudflare.setup_tunnel(service="...", port=0, hostname="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `service` | string | yes | — | Service name (must match the app service name in docker-compose.yml). |
| `port` | integer | yes | — | Port the service listens on inside the container. |
| `hostname` | string | yes | — | Public hostname in subdomain.domain format (e.g. archi-mcp.matthewdart.name). |
| `network_mode` | string | no | `"service"` | Networking strategy: 'service' (cloudflared shares app network namespace) or 'host' (both use host networking). Values: `service`, `host`. |
| `output_dir` | string? | no | — | Directory to write generated files. If null, no files are written. |
| `dry_run` | boolean | no | `false` | If true, generate config strings but do not write any files even if output_dir is set. |

## Error Codes

| Code | Description |
|------|-------------|
| `invalid_hostname` | Hostname is not in subdomain.domain format. |

## Side Effects

Optionally writes cloudflared-compose-block.yml and cloudflared-env-block.txt to the specified output directory. Does not interact with the Cloudflare API.
