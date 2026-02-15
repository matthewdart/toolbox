# Fleet Health Check

## When to use

- After deploying any MCP service (remarkable-pipeline, health-ledger, archi-mcp-bridge)
- When an MCP tool call fails or returns unexpected errors
- Proactively during troubleshooting sessions involving remote services
- When the user asks about service status, uptime, or connectivity

## How to use

Call the `infra.fleet_health` capability via MCP:

```
infra.fleet_health(scope="full")
```

### Scopes

- `local` — SSH to the VM, checks container status + health endpoint + MCP smoke test
- `tunnel` — Via Cloudflare public HTTPS, checks health + MCP reachability
- `full` — Both local and tunnel (recommended for post-deploy verification)

### Interpreting results

- `fleet_status: "ok"` — All services healthy across all checked surfaces
- `fleet_status: "degraded"` — Some non-critical checks failed (external APIs unreachable, tunnel issues)
- `fleet_status: "error"` — Critical failures (containers down, health endpoint returning error, DuckDB missing)

### Per-service checks

**Local checks** (short-circuit on critical failure):
1. Container running? (`docker compose ps`)
2. Health endpoint returns ok/degraded? (`curl localhost:<port>/health`)
3. MCP smoke test succeeds? (real `tools/call` JSON-RPC request)

**Tunnel checks**:
1. Health reachable via HTTPS? (`curl https://<hostname>/health`)
2. MCP endpoint reachable? (`POST https://<hostname>/mcp`)

### Filtering to specific services

```
infra.fleet_health(scope="local", services=["health-ledger"])
```

## Service registry

| Service | Port | Smoke tool | Hostname |
|---------|------|-----------|----------|
| remarkable-pipeline | 8766 | `remarkable_status` | remarkable-pipeline-mcp.matthewdart.name |
| health-ledger | 8765 | `list_assets` | health-ledger.matthewdart.name |
| archi-mcp-bridge | 8767 | `jarchi_catalog` | archi-mcp-bridge.matthewdart.name |
