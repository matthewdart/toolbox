# Cloudflare Tunnel Sidecar — Operational Guide

How to add Cloudflare Tunnel exposure to a Docker Compose service in this ecosystem.

Architectural pattern: [handbook REFERENCE_ARCHITECTURE.md §11.6](https://github.com/matthewdart/handbook/blob/main/REFERENCE_ARCHITECTURE.md#116-cloudflare-tunnel-sidecar-pattern)

---

## Prerequisites

- Cloudflare account with Zero Trust enabled
- Domain managed by Cloudflare (`matthewdart.name`)
- Service already containerised with a `docker-compose.yml`

---

## Strategy Decision

Choose based on service requirements:

### Shared namespace (default)

`network_mode: "service:<app>"` — cloudflared shares the app container's network stack. The app binds to `localhost`, cloudflared reaches it at `localhost:<port>`.

Use when: the service only needs to serve HTTP and has no host-level dependencies.

Used by: `archi-mcp-bridge`, `health-ledger`

### Host networking

`network_mode: host` — both app and cloudflared use host networking.

Use when: the app needs access to host-level resources (e.g. Tailscale for SSH to a device).

Used by: `remarkable-pipeline`

---

## docker-compose.yml Templates

### Shared namespace

```yaml
services:
  my-service:
    image: ghcr.io/matthewdart/my-service:latest
    container_name: my-service
    restart: unless-stopped
    env_file: [.env]
    volumes:
      - ./data:/app/data

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: my-service-tunnel
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CF_TUNNEL_TOKEN}
    network_mode: "service:my-service"
    depends_on:
      - my-service
```

### Host networking

```yaml
services:
  my-service:
    image: ghcr.io/matthewdart/my-service:latest
    container_name: my-service
    restart: unless-stopped
    env_file: [.env]
    volumes:
      - ./data:/app/data
    network_mode: host

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: my-service-tunnel
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CF_TUNNEL_TOKEN}
    network_mode: host
    depends_on:
      - my-service
```

---

## Dashboard Setup

1. Go to **Cloudflare Zero Trust** > **Networks** > **Tunnels**
2. Select **Create a tunnel**
3. Name the tunnel (e.g. `my-service`)
4. Copy the tunnel token
5. Paste it into `.env` as `CF_TUNNEL_TOKEN=<token>`
6. Under the tunnel's **Public Hostname** tab, add a route:
   - Subdomain: `my-service`
   - Domain: `matthewdart.name`
   - Service: `http://localhost:<port>`
7. Save

---

## .env Configuration

```bash
# Dedicated tunnel token for this service.
# Create in: Cloudflare Zero Trust > Networks > Tunnels > Create
# Configure public hostname to route to http://localhost:<port>
CF_TUNNEL_TOKEN=
```

---

## Verification

```bash
# Check tunnel container is running
docker compose logs cloudflared | tail -20

# Test locally (shared namespace only)
curl -fsS http://localhost:<port>/health

# Test via public hostname
curl -fsS https://my-service.matthewdart.name/health

# Check Cloudflare dashboard: tunnel status should show "Connected"
```

---

## Toolbox Capability

Generate config with the `cloudflare.setup_tunnel` capability:

```bash
python -m core.dispatch --capability cloudflare.setup_tunnel --input-json '{
  "service": "my-service",
  "port": 8080,
  "hostname": "my-service.matthewdart.name"
}'
```

Or invoke via MCP when the toolbox server is configured in `.mcp.json`.

---

## MCP SDK v1.26 Compatibility

Services using the Python MCP SDK (`mcp` package) v1.26+ need these adjustments when accessed via Cloudflare Tunnels:

### DNS Rebinding Protection

The SDK enables DNS rebinding protection by default, only allowing `localhost`, `127.0.0.1`, and `[::1]` as `Host` headers. Requests from Cloudflare Tunnels arrive with the public hostname (e.g. `Host: health-ledger.matthewdart.name`), causing HTTP 421 Misdirected Request.

**Fix:** Disable DNS rebinding protection — Cloudflare Zero Trust handles auth at the edge:

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

mcp = FastMCP(
    "my-server",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)
```

### Bearer Token Auth

If the service enforces bearer token authentication, the Cloudflare MCP Portal sync cannot authenticate (it doesn't know the token). Since Zero Trust handles access control at the Cloudflare edge, skip bearer auth for the `/mcp` endpoint:

```python
# In BearerTokenMiddleware
path = scope.get("path", "")
if path in ("/health", "/mcp"):
    await self._app(scope, receive, send)
    return
```

### Custom Routes (Health Endpoint)

Use `@mcp.custom_route("/health")` instead of nesting Starlette apps via `Mount()`. The SDK's `streamable_http_app()` creates its own Starlette app with an internal `/mcp` route — wrapping it with `Mount("/mcp", ...)` creates a `/mcp/mcp` double-path. Nesting with `Mount("/", ...)` breaks lifespan propagation.

```python
@mcp.custom_route("/health", methods=["GET"])
async def _health(request):
    return JSONResponse({"status": "ok"})

app = mcp.streamable_http_app()  # Use directly, don't wrap
```

---

## Relationship to MCP Portals

Tunnels provide connectivity (service → internet). MCP Portals aggregate multiple MCP servers behind a single endpoint with access control. Both layers are complementary.

See: [docs/mcp-portal-pattern.md](mcp-portal-pattern.md)
