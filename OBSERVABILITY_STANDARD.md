# Observability Standard — Principles, Rules, and Per-Service Expectations

## Scope and Role

This document defines the **observability conventions** that all services in the ecosystem are expected to follow.

It codifies what was previously implicit in [OWNER_PREFERENCES.md](OWNER_PREFERENCES.md) and [REFERENCE_ARCHITECTURE.md](REFERENCE_ARCHITECTURE.md) into explicit, auditable requirements. It does not introduce heavy observability infrastructure. The goal is **diagnostic capability at low cost** — enough to detect, locate, and understand failures without attaching a debugger or adding opaque tooling.

It answers one question:

> **Can I tell what this service is doing, whether it is healthy, and why it failed — from the outside?**

---

## Relationship to Other Governance Artifacts

- **[Tech Constitution](TECH_CONSTITUTION.md)** — Invariant 2 (Explicit Causality) and Invariant 5 (Explicit Boundaries) are the constitutional basis for observability. Behaviour must be explainable; effects must be identifiable at boundaries.
- **[Reference Architecture](REFERENCE_ARCHITECTURE.md)** — §11.8 defines `/health` endpoints, port registry, and `HEALTHCHECK` conventions. This document extends those into a broader observability framework.
- **[Owner Preferences](OWNER_PREFERENCES.md)** — §Execution and Observability defines the active observation philosophy. This document makes that philosophy enforceable.
- **[Playbook](PLAYBOOK.md)** — §5 defines the audit framework. An [Observability Audit](audits/OBSERVABILITY_AUDIT.md) provides the verification mechanism.

---

## General Principles

These principles apply to all services, scripts, and pipelines in the ecosystem.

### 1. Silent failure is prohibited

Every failure path must produce diagnostic output. A process that fails silently is broken regardless of whether its logic is correct. This is the single non-negotiable observability rule.

### 2. Observability is structural, not ornamental

Observability is not added after the fact. It is part of the service contract — the same way a `/health` endpoint is part of the API surface. If a service cannot explain its own state, it is incomplete.

### 3. Output over instrumentation

Prefer direct, readable output (stdout/stderr, structured JSON, log lines) over framework-mediated telemetry. The goal is diagnosis by a human or agent reading output, not dashboard construction.

### 4. Boundaries are the observation surface

Observe at system boundaries: startup, shutdown, request handling, external calls, error paths. Internal function-level tracing is not required. If boundary behaviour is clear, internals can be reasoned about.

### 5. Health is queryable, not inferred

Every long-running service must answer "are you healthy?" via a standard endpoint. Health is not inferred from the absence of errors — it is actively reported.

### 6. Enough to diagnose, not enough to reconstruct

Services should log enough to identify what happened and where it failed. They are not required to produce a full replay log. The target is **diagnostic sufficiency**, not completeness.

---

## Rules — All Services

These rules apply to every Dockerised MCP service in the ecosystem (health-ledger, remarkable-pipeline, archi-mcp-bridge, pptx-mcp-bridge, and any future services).

### R1. Health endpoint

Every service MUST expose `GET /health` returning JSON without authentication.

**Minimum response:**

```json
{"status": "ok"}
```

**Recommended response (when practical):**

```json
{
  "status": "ok",
  "service": "<service-name>",
  "version": "<version-or-commit>",
  "uptime_seconds": 3742
}
```

The `version` field SHOULD be the git commit SHA or a semver tag, injected at build time. This eliminates "which version is deployed?" as a diagnostic question.

### R2. Docker HEALTHCHECK

Every Dockerfile MUST include a `HEALTHCHECK` instruction:

```dockerfile
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:${HTTP_PORT}/health || exit 1
```

This is already defined in [REFERENCE_ARCHITECTURE.md §11.8](REFERENCE_ARCHITECTURE.md). Restated here for completeness.

### R3. Startup banner

Every service MUST log a startup banner to stdout when it begins accepting requests. The banner MUST include:

- Service name
- Listening address and port
- Version or commit (if available)

**Example:**

```
health-ledger listening on 127.0.0.1:8765 (abc1234)
```

This confirms the service started, on the expected port, with the expected version. It costs one line of code and eliminates an entire class of "is it running?" questions.

### R4. Startup configuration echo

Every service SHOULD log its effective configuration on startup (after defaults are applied and environment variables are resolved). This MUST NOT include secret values — secrets should be logged as present/absent, not their content.

**Example:**

```
config: HTTP_PORT=8765 HTTP_HOST=127.0.0.1 BEARER_AUTH=enabled DATA_DIR=/data
```

### R5. Request logging

Every service SHOULD log inbound requests at the boundary level. The minimum useful fields are:

- HTTP method and path
- Response status code
- Duration (milliseconds)

**Example:**

```
POST /mcp 200 42ms
GET /health 200 1ms
```

Request logging MAY be omitted for `/health` requests to reduce noise.

Verbose request/response body logging is NOT required and NOT recommended by default. It should be available as a debug toggle (e.g. an environment variable), not a permanent fixture.

### R6. Error output

When a request fails or an internal error occurs, the service MUST log:

- What operation was attempted
- What went wrong (the error message or exception)
- Enough context to identify the trigger (request path, input identifier, etc.)

**Example:**

```
error: POST /mcp tool=import_records — FileNotFoundError: /data/input/export.zip not found
```

Stack traces SHOULD be logged for unexpected errors (500-class). Expected client errors (4xx) do not require stack traces.

### R7. Shutdown logging

Every service SHOULD log when it receives a shutdown signal and when it completes shutdown. This distinguishes intentional stops from crashes.

**Example:**

```
received SIGTERM, shutting down
shutdown complete
```

---

## Rules — Scripts and Pipelines

For non-service code (build scripts, data pipelines, one-shot tools):

### R8. Progress indication

Scripts that process multiple items SHOULD indicate progress. A count or percentage at reasonable intervals is sufficient.

**Example:**

```
processing 47/128 records...
```

### R9. Summary on completion

Scripts SHOULD print a summary line on successful completion, including counts of items processed, created, skipped, or failed.

**Example:**

```
done: 128 records processed, 3 skipped, 0 errors
```

### R10. Non-zero exit on failure

Scripts MUST exit with a non-zero status code on failure. This is a baseline requirement for any automated pipeline.

---

## Rules — Verification and Deployment

### R11. Post-deployment verification

After deploying or restarting a service, the deployer (human or CI) MUST verify health by querying the `/health` endpoint and confirming a successful response. This is already stated in [OWNER_PREFERENCES.md](OWNER_PREFERENCES.md) — restated here as an explicit rule.

### R12. Log review after deployment

After deploying or restarting a service, the deployer SHOULD review recent logs (e.g. `docker logs --tail 20 <container>`) to confirm the startup banner appeared, no errors occurred during initialisation, and the service is accepting requests.

---

## What This Standard Does Not Require

The following are **explicitly not required** and should not be introduced without passing the [tool admission checklist](MANIFESTO.md):

- Logging frameworks (e.g. structlog, loguru, winston, pino). Print-based logging with consistent format is sufficient.
- Metrics collection infrastructure (Prometheus, StatsD, Datadog agents).
- Distributed tracing (OpenTelemetry, Jaeger, Zipkin).
- Centralised log aggregation (ELK, Splunk, CloudWatch Logs).
- APM tools (New Relic, Datadog APM).
- Alerting infrastructure (PagerDuty, Opsgenie).

These tools may be adopted in the future if the forward test is passed: *"Will this increase insight per unit of effort — or just surface area?"* Until then, the standard is diagnostic output, health endpoints, and active human/agent observation.

---

## Per-Service Checklist

Use this checklist when building or auditing a service. Every service should satisfy all MUST items and most SHOULD items.

| # | Rule | Level | Check |
|---|------|-------|-------|
| R1 | Health endpoint (`GET /health`, no auth, JSON) | MUST | |
| R2 | Docker `HEALTHCHECK` instruction | MUST | |
| R3 | Startup banner (name, address, version) | MUST | |
| R4 | Startup config echo (no secrets) | SHOULD | |
| R5 | Request logging (method, path, status, duration) | SHOULD | |
| R6 | Error output (operation, error, context) | MUST | |
| R7 | Shutdown logging | SHOULD | |
| R8 | Progress indication (scripts/pipelines) | SHOULD | |
| R9 | Completion summary (scripts/pipelines) | SHOULD | |
| R10 | Non-zero exit on failure (scripts/pipelines) | MUST | |
| R11 | Post-deployment health check | MUST | |
| R12 | Post-deployment log review | SHOULD | |

---

## Living Status

This standard is expected to evolve.

Revise it when:

- Failures occur that could not be diagnosed with the current conventions
- A new service pattern emerges that these rules do not cover
- The cost of manual observation exceeds the cost of automated collection

When that happens, update this document — not just individual implementations.
