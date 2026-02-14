# Cloudflare MCP Portal — Operational Guide

How to set up a Cloudflare MCP Portal to aggregate multiple MCP servers behind a single endpoint.

Architectural pattern: [handbook REFERENCE_ARCHITECTURE.md §11.7](https://github.com/matthewdart/handbook/blob/main/REFERENCE_ARCHITECTURE.md#117-mcp-server-aggregation-cloudflare-mcp-portal)

---

## What MCP Portals Do

- Single portal URL replaces multiple per-service MCP endpoint URLs
- Zero Trust access policies (identity, device posture, MFA)
- OAuth-based user authentication
- Unified audit logging for all MCP requests
- Automatic capability synchronisation every 24 hours
- Per-server tool and prompt curation

---

## Full Setup Checklist

Getting an MCP server visible through the portal requires **five layers** to be consistent. Each depends on the one above it.

```
1. Tunnel ingress     hostname → localhost:<port>
2. DNS CNAME          hostname → <tunnel-uuid>.cfargotunnel.com
3. MCP Server         registered with https://<hostname>/mcp
4. Access Application auto-created (type: mcp) with access policy
5. Portal assignment  server explicitly added to the portal's server list
```

### Layer 1: Tunnel Ingress

The Cloudflare Tunnel sidecar must have an ingress rule routing the public hostname to the local service port. Configure via API or dashboard.

See: [cloudflare-tunnel-pattern.md](cloudflare-tunnel-pattern.md)

### Layer 2: DNS CNAME

A proxied CNAME record `<hostname>` → `<tunnel-uuid>.cfargotunnel.com` must exist in the Cloudflare DNS zone. Without this, requests get HTTP 530.

### Layer 3: MCP Server Registration

Register the server in Cloudflare AI Controls with the public hostname URL (e.g. `https://health-ledger.matthewdart.name/mcp`). The hostname in the registration must exactly match the tunnel ingress and DNS.

### Layer 4: Access Application

When a server is added via the dashboard, an Access Application (`type: mcp`) is auto-created with an access policy. When adding via API, verify the application exists and has appropriate policies.

### Layer 5: Portal Assignment

**Servers must be explicitly assigned to a portal.** Registering a server does not automatically add it to any portal. Use `update_portal_servers` to manage the assignment.

---

## Prerequisites

- MCP servers already exposed via Cloudflare Tunnels (see [cloudflare-tunnel-pattern.md](cloudflare-tunnel-pattern.md))
- Cloudflare One / Zero Trust subscription
- Identity provider configured in Cloudflare Access
- `CLOUDFLARE_API_TOKEN` — API token with Zero Trust permissions (or `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL` for Global API Key auth)
- `CLOUDFLARE_ACCOUNT_ID` — Cloudflare account ID (used as default by the capability)

---

## Setup Steps

### 1. Create Portal

1. Go to **Cloudflare One** > **Access controls** > **AI controls**
2. Select **Add MCP server portal**
3. Enter a portal name
4. Choose a Cloudflare domain and optional subdomain
5. The portal URL will be `https://<subdomain>.<domain>/mcp`

### 2. Register MCP Servers

Via the toolbox capability (preferred):

```bash
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{
  "command": "add_server",
  "name": "health-ledger",
  "url": "https://health-ledger.matthewdart.name/mcp"
}'
```

Or via the dashboard:

1. Go to **AI controls** > **MCP servers** tab
2. Select **Add an MCP server**
3. Enter the server name and its tunnel URL (e.g. `https://archi-mcp-bridge.matthewdart.name/mcp`)
4. Apply access policies
5. Authenticate if the server uses OAuth
6. Wait for status to show **Ready**

### 3. Assign Servers to Portal

Registering a server does **not** automatically add it to a portal. Assign servers explicitly:

```bash
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{
  "command": "update_portal_servers",
  "portal_id": "mcp-portal",
  "server_ids": ["archi-mcp-bridge", "remarkable-pipeline-mcp", "health-ledger"]
}'
```

**Warning:** `update_portal_servers` **replaces** the entire server list. Always include all servers you want assigned.

### 4. Configure Access Policies

Each portal and each server must have an Access policy. Configure:

- Identity requirements (which users/groups can access)
- Device posture checks
- MFA requirements
- Session duration

### 5. Distribute Portal URL

Give clients the single portal URL. They configure it in their MCP client:

```json
{
  "mcpServers": {
    "my-portal": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://<subdomain>.<domain>/mcp"]
    }
  }
}
```

---

## Capability Management

- Cloudflare syncs with each MCP server every 24 hours
- Manual sync via toolbox capability: `{"command": "sync_server", "server_id": "<server-id>"}`
- Manual sync via dashboard: **AI controls** > **MCP servers** tab > three dots > **Sync capabilities**
- New tools and prompts are automatically enabled
- Admins can disable specific tools per server in the portal

---

## Common Failure Modes

| Symptom | Layer | Root Cause | Fix |
|---|---|---|---|
| HTTP 503 | 1 (Tunnel) | No ingress rule for hostname | Add ingress rule via tunnel config API or dashboard |
| HTTP 530 | 2 (DNS) | Missing or wrong DNS CNAME | Create proxied CNAME → `<tunnel-uuid>.cfargotunnel.com` |
| HTTP 404 | 3 (Server) | Hostname mismatch between server registration and tunnel | Update server URL to match tunnel hostname |
| HTTP 421 | App | MCP SDK DNS rebinding protection blocks non-localhost Host headers | Set `enable_dns_rebinding_protection=False` in `TransportSecuritySettings` |
| "Authorization failed" | App | Bearer token auth blocks portal sync requests | Skip bearer auth for `/mcp` path (Zero Trust handles access) |
| Server ready but not in portal | 5 (Portal) | Server registered but not assigned to portal | Use `update_portal_servers` to assign it |
| Sync shows error | 3 (Server) | Server URL unreachable from Cloudflare edge | Check all 5 layers in order |

---

## End-to-End Verification

Use the `verify_portal` command to check that all servers are correctly configured and reachable. This runs four checks per registered server:

1. **Registration status** — server `status` is `ready` in the Cloudflare API
2. **Portal assignment** — server is present in the portal's server list
3. **Health endpoint** — `GET <hostname>/health` returns a successful response
4. **MCP endpoint** — `POST <hostname>/mcp` is reachable (any HTTP response means the server is up; only connection/timeout errors indicate failure)

```bash
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{
  "command": "verify_portal",
  "portal_id": "mcp-portal"
}'
```

The response includes an `all_ok` flag and per-server check details. Use this after adding or modifying servers to confirm the full 5-layer stack is working.

---

## Portal Logs

Monitor activity: **AI controls** > find the portal or server > three dots > **Edit** > **Logs**

Logs include individual requests, tool invocations, and authentication events.

---

## Toolbox Capability

Manage MCP servers and portals via the `infra.setup_mcp_portal` capability. The `account_id` parameter defaults to the `CLOUDFLARE_ACCOUNT_ID` environment variable.

```bash
# List registered servers
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "list_servers"}'

# List portals
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "list_portals"}'

# Get portal detail (including assigned server list)
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "get_portal", "portal_id": "mcp-portal"}'

# Register a new server
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{
  "command": "add_server",
  "name": "health-ledger",
  "url": "https://health-ledger.matthewdart.name/mcp"
}'

# Update a server's URL
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{
  "command": "update_server",
  "server_id": "health-ledger",
  "url": "https://health-ledger.matthewdart.name/mcp"
}'

# Sync capabilities
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "sync_server", "server_id": "health-ledger"}'

# Assign servers to portal (replaces full list)
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{
  "command": "update_portal_servers",
  "portal_id": "mcp-portal",
  "server_ids": ["archi-mcp-bridge", "remarkable-pipeline-mcp", "health-ledger"]
}'

# Verify portal end-to-end (registration, assignment, health, MCP probes)
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "verify_portal", "portal_id": "mcp-portal"}'

# Remove a server
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "remove_server", "server_id": "health-ledger"}'
```

Requires `CLOUDFLARE_ACCOUNT_ID` and either `CLOUDFLARE_API_TOKEN` or `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL`. No external dependencies.

---

## Relationship to Tunnels

Tunnels and portals are complementary layers:

- **Cloudflare Tunnels** provide connectivity (service → internet)
- **Cloudflare MCP Portals** provide aggregation and access control (multiple MCP services → one client endpoint)

Portals do not replace tunnels — each MCP server still needs its own tunnel.
