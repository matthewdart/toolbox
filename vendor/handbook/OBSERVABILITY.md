# Observability Conventions

Durable conventions for structured logging, health endpoints, request tracing, and deployment verification across all containerised MCP services.

---

## 1. Structured Logging

All services emit JSON lines to stdout with this envelope:

```json
{"ts": "2026-02-15T12:00:00.000Z", "level": "INFO", "logger": "module.name", "msg": "message"}
```

| Field | Format | Notes |
|---|---|---|
| `ts` | ISO 8601 UTC | Always UTC, never local time |
| `level` | `DEBUG`, `INFO`, `WARN`, `ERROR` | Uppercase |
| `logger` | Module identifier | e.g. `hla.api`, `remarkable_pipeline.mcp.http` |
| `msg` | Human-readable message | Structured key=value pairs for machine-parseable fields |

Additional context fields are top-level keys (not nested). The Docker `json-file` log driver wraps each line, so aggregators see JSON-in-JSON.

**Silent failure is not acceptable.** Every `catch` block must either re-raise, return a structured error, or log at WARN/ERROR. Silent `catch(Exception ignore)` patterns are banned.

---

## 2. Request Logging

Every HTTP service logs every request (excluding `/health`) with:

```json
{"ts": "...", "level": "INFO", "logger": "...", "msg": "request", "method": "POST", "path": "/mcp", "status": 200, "duration_ms": 45}
```

Implementation:
- **Python (ASGI)**: Middleware wrapping the Starlette/FastAPI app, capturing method, path, status code, and duration
- **Java (HttpServer)**: In the handler's `finally` block, excluding `/health`

---

## 3. Health Endpoint Contract

Every containerised service exposes `GET /health` (unauthenticated).

### Response shape

```json
{
  "status": "ok",
  "uptime": "123s",
  "service": "service-name",
  "checks": {
    "check_name": true,
    "another_check": 42
  }
}
```

### Status semantics

| Status | HTTP code | Meaning |
|---|---|---|
| `"ok"` | 200 | All checks pass — service is fully functional |
| `"degraded"` | 200 | Non-critical checks failed — service works but with limitations |
| `"error"` | 503 | Critical checks failed — service cannot function |

### Health check depth

Health endpoints must probe **every external edge** the service depends on:

- **Data layer**: Database/file exists? Queryable? Tables populated?
- **External APIs**: Reachable with timeout? (Use background cache — never block `/health` on network I/O)
- **Configuration**: Required env vars present? Expected files exist?

A simple `{"status": "ok"}` with no checks is not acceptable — it hides data layer failures, missing files, and broken dependencies.

### Background health cache

External API checks (OpenAI, reMarkable Connect, etc.) run in a background thread every 30s. The `/health` endpoint serves cached values instantly. This prevents:
- Health check timeouts from propagating to callers
- Thundering-herd problems under monitoring
- Blocking the event loop on network I/O

---

## 4. Docker Compose Conventions

All `docker-compose.yml` files include resource limits and log rotation:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512m    # Service-specific
          cpus: "1.0"     # Service-specific
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  cloudflared:
    deploy:
      resources:
        limits:
          memory: 128m
    logging:
      driver: json-file
      options:
        max-size: "5m"
        max-file: "2"
```

| Service | App memory | App CPUs | Sidecar memory |
|---|---|---|---|
| remarkable-pipeline | 512m | 1.0 | 128m |
| health-ledger | 1g | 1.0 | 128m |
| archi-mcp-bridge | 1g | 2.0 | 128m |

---

## 5. CI/CD Deployment Verification

The `deploy-stack.yml` reusable workflow polls `GET /health` after deploy:

```yaml
health_port: 8766      # 0 = skip health check
health_timeout: 120     # seconds
```

The deploy step:
1. Polls `localhost:<port>/health` via SSH every 5 seconds
2. Accepts `"ok"` or `"degraded"` status
3. On timeout: dumps `docker compose logs --tail=50` and fails the workflow

This catches "container running but service not functional" deploy failures.

---

## 6. Fleet Health

The `infra.fleet_health` toolbox capability verifies all services across local (SSH) and tunnel (Cloudflare HTTPS) surfaces. Three scopes:

- **local**: Container status + health endpoint + MCP smoke test (via SSH)
- **tunnel**: Health probe + MCP reachability (via Cloudflare HTTPS)
- **full**: Both local and tunnel

Use after deploys, on tool failures, or proactively during troubleshooting.
