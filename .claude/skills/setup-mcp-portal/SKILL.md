---
name: setup-mcp-portal
description: Manage Cloudflare MCP Portal servers and portals via the Cloudflare API. Supports listing, adding, updating, syncing, and removing servers, managing portal-to-server assignments, and verifying end-to-end portal health.
---

# Setup Mcp Portal

Manage Cloudflare MCP Portal servers and portals via the Cloudflare API. Supports listing, adding, updating, syncing, and removing servers, managing portal-to-server assignments, and verifying end-to-end portal health.

## Invocation

Call the `cloudflare.setup_mcp_portal` capability via MCP:

```
cloudflare.setup_mcp_portal(command="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `command` | string | yes | — | The subcommand to execute. Values: `list_servers`, `list_portals`, `get_portal`, `add_server`, `update_server`, `sync_server`, `remove_server`, `update_portal_servers`, `verify_portal`. |
| `account_id` | string? | no | — | Cloudflare account ID. Defaults to CLOUDFLARE_ACCOUNT_ID env var if not provided. |
| `name` | string? | no | — | Display name for the MCP server. Required for add_server. |
| `url` | string? | no | — | MCP server URL (e.g. https://host/mcp). Required for add_server, optional for update_server. |
| `auth_type` | string? | no | `"unauthenticated"` | Auth type for the MCP server (default: unauthenticated). Used by add_server and update_server. |
| `server_id` | string? | no | — | Server ID. Required for sync_server, remove_server, and update_server. Optional for add_server (defaults to name). |
| `portal_id` | string? | no | — | Portal ID. Required for get_portal, update_portal_servers, and verify_portal. |
| `server_ids` | array? | no | — | List of server IDs to assign to the portal. Required for update_portal_servers. Replaces the full server list. |

## Error Codes

| Code | Description |
|------|-------------|
| `auth_error` | Cloudflare credentials not found in environment variables. |
| `validation_error` | Missing or invalid parameters for the requested command. |
| `api_error` | Cloudflare API returned an error response. |

## Side Effects

Registers, updates, syncs, or removes MCP servers and portal assignments in the Cloudflare account via API calls. List and get commands are read-only.
