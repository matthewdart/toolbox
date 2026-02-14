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

## Prerequisites

- MCP servers already exposed via Cloudflare Tunnels (see [cloudflare-tunnel-pattern.md](cloudflare-tunnel-pattern.md))
- Cloudflare One / Zero Trust subscription
- Identity provider configured in Cloudflare Access
- `CLOUDFLARE_API_TOKEN` — API token with Zero Trust permissions (or `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL` for Global API Key auth)
- `CLOUDFLARE_ACCOUNT_ID` — Cloudflare account ID

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
  "url": "https://health-ledger-mcp.matthewdart.name/mcp"
}'
```

Or via the dashboard:

1. Go to **AI controls** > **MCP servers** tab
2. Select **Add an MCP server**
3. Enter the server name and its tunnel URL (e.g. `https://archi-mcp.matthewdart.name/mcp`)
4. Apply access policies
5. Authenticate if the server uses OAuth
6. Wait for status to show **Ready**

### 3. Configure Access Policies

Each portal and each server must have an Access policy. Configure:

- Identity requirements (which users/groups can access)
- Device posture checks
- MFA requirements
- Session duration

### 4. Distribute Portal URL

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
- Manual sync via toolbox skill: `setup_mcp_portal sync-server --id <server-id>`
- Manual sync via dashboard: **AI controls** > **MCP servers** tab > three dots > **Sync capabilities**
- New tools and prompts are automatically enabled
- Admins can disable specific tools per server in the portal

---

## Portal Logs

Monitor activity: **AI controls** > find the portal or server > three dots > **Edit** > **Logs**

Logs include individual requests, tool invocations, and authentication events.

---

## Toolbox Capability

Manage MCP servers and portals via the `infra.setup_mcp_portal` capability:

```bash
# List registered servers
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "list_servers"}'

# List portals
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "list_portals"}'

# Register a new server
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{
  "command": "add_server",
  "name": "health-ledger",
  "url": "https://health-ledger-mcp.matthewdart.name/mcp"
}'

# Sync capabilities
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "sync_server", "id": "health-ledger"}'

# Remove a server
python -m core.dispatch --capability infra.setup_mcp_portal --input-json '{"command": "remove_server", "id": "health-ledger"}'
```

Requires `CLOUDFLARE_ACCOUNT_ID` and either `CLOUDFLARE_API_TOKEN` or `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL`. No external dependencies.

---

## Relationship to Tunnels

Tunnels and portals are complementary layers:

- **Cloudflare Tunnels** provide connectivity (service → internet)
- **Cloudflare MCP Portals** provide aggregation and access control (multiple MCP services → one client endpoint)

Portals do not replace tunnels — each MCP server still needs its own tunnel.
