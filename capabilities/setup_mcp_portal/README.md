# infra.setup_mcp_portal

## Description

Manage Cloudflare MCP Portal servers and portals via the Cloudflare API. Supports five subcommands: listing servers, listing portals, adding a server, syncing a server's capabilities, and removing a server.

## Authentication

Reads credentials from environment variables. Supports two modes:

- **API Token**: `CLOUDFLARE_API_TOKEN`
- **Global Key**: `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL`

If neither is set, raises `AuthError`.

## Commands

| Command | Required params | Description |
|---|---|---|
| `list_servers` | `account_id` | List all registered MCP servers |
| `list_portals` | `account_id` | List all MCP portals |
| `add_server` | `account_id`, `name`, `url` | Register a new MCP server |
| `sync_server` | `account_id`, `server_id` | Trigger capability sync for a server |
| `remove_server` | `account_id`, `server_id` | Delete an MCP server registration |

## Non-goals

- Managing portal configuration or access policies
- Handling OAuth or other auth flows for MCP servers
- Managing Cloudflare Access applications or tunnels

## Deterministic behavior

Given the same inputs, the capability sends the same API request. The outcome depends on remote Cloudflare account state and is therefore not fully deterministic.
