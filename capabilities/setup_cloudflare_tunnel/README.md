# infra.setup_cloudflare_tunnel

## Description

Generate Cloudflare Tunnel sidecar configuration for a Docker Compose service. Produces a `cloudflared` compose service block, a `.env` template with `CF_TUNNEL_TOKEN`, and human-readable dashboard setup instructions.

## Non-goals

- Interacting with the Cloudflare API or creating tunnels programmatically
- Managing tunnel tokens or secrets
- Modifying existing `docker-compose.yml` files in place
- DNS record creation or validation

## Deterministic behavior

Given the same service name, port, hostname, and network mode, the capability always produces identical compose blocks, env templates, and instructions. File writing depends on whether `output_dir` is set and `dry_run` is false.
