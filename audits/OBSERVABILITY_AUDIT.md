# Observability Audit — Prompt

## Purpose

This prompt is intended to be given to a coding agent with access to one or more service repositories. Its task is to audit each service against the [Observability Standard](../OBSERVABILITY_STANDARD.md), verifying that the required conventions are implemented and identifying gaps.

This is a **diagnostic audit**. Evidence precedes recommendations. The output should surface concrete findings, not opinions.

---

## Prompt

You are auditing one or more service repositories against the ecosystem Observability Standard. Your task is to verify that each service implements the required observability conventions and to identify gaps, partial implementations, and deviations.

Base all conclusions on evidence from the codebase. Do not infer behaviour from framework defaults — verify it in code.

## Scope

This audit applies to:

- Dockerised MCP services (health-ledger, remarkable-pipeline, archi-mcp-bridge, pptx-mcp-bridge, and any future services)
- Scripts and pipelines within those repositories
- Deployment configurations (Dockerfile, docker-compose.yml, CI/CD workflows)

## Pre-flight

Before inspecting individual rules:

1. **Identify the service** — name, language, framework (if any), entry point file.
2. **Locate the Dockerfile** and `docker-compose.yml`.
3. **Identify the HTTP server setup** — where the server is initialised, where routes are registered.
4. **Identify the main entry point** — what runs when the container starts.

Present the inventory before proceeding.

## What to inspect (mandatory)

For each rule in the Observability Standard, inspect the codebase and classify the finding.

### R1. Health endpoint

- Does a `GET /health` route exist?
- Does it return JSON with at least `{"status": "ok"}`?
- Does it require authentication? (It must not.)
- Does the response include `service`, `version`, or `uptime_seconds`? (Recommended, not required.)
- Quote the relevant code.

### R2. Docker HEALTHCHECK

- Does the Dockerfile contain a `HEALTHCHECK` instruction?
- Does it target the `/health` endpoint?
- Does it use the `${HTTP_PORT}` variable?
- Quote the instruction.

### R3. Startup banner

- Does the service log a startup message when it begins listening?
- Does the message include service name, address/port, and version?
- Quote the relevant code.

### R4. Startup configuration echo

- Does the service log its effective configuration on startup?
- Are secret values redacted (logged as present/absent, not raw values)?
- Quote the relevant code, or note absence.

### R5. Request logging

- Is there middleware or handler-level logging of inbound requests?
- Does it include method, path, status code, and duration?
- Is `/health` request logging suppressed or included?
- Quote the relevant code, or note absence.

### R6. Error output

- When a request handler or internal operation fails, is the error logged?
- Does the log include what operation was attempted, the error message, and contextual identifiers?
- Are stack traces logged for unexpected errors?
- Quote an example from the codebase.

### R7. Shutdown logging

- Does the service log receipt of shutdown signals (SIGTERM, SIGINT)?
- Does it log completion of shutdown?
- Quote the relevant code, or note absence.

### R8–R9. Scripts and pipelines (if applicable)

- Do scripts in the repository produce progress output?
- Do scripts print a summary on completion?
- Quote examples, or note absence.

### R10. Non-zero exit on failure

- Do scripts exit with non-zero on failure?
- Check for bare `except` blocks that swallow errors, or `sys.exit(0)` in error paths.

### R11–R12. Deployment verification

- Does the CI/CD workflow (GitHub Actions) or deploy script include a post-deployment health check?
- Is there any automated log review after deployment?
- If not automated, is there documentation instructing manual verification?

## Scoring

For each rule, classify as:

| Status | Meaning |
|--------|---------|
| **Conformant** | Fully implemented as specified |
| **Partial** | Implemented but missing recommended elements |
| **Non-conformant** | Not implemented or implemented incorrectly |
| **N/A** | Rule does not apply to this service type |

## Output format

Produce the audit in the following structure:

### 1. Service inventory

Table: service name, language, entry point, HTTP framework, Dockerfile location.

### 2. Per-rule findings

For each of R1–R12:

- **Status:** Conformant / Partial / Non-conformant / N/A
- **Evidence:** Code quote or file reference
- **Notes:** Any observations (e.g. "version field is hardcoded, not injected at build time")

### 3. Summary scorecard

Table: rule number, rule name, status. One row per rule.

### 4. Gap analysis

Ordered list of non-conformant and partial items, prioritised by:

1. MUST rules that are non-conformant (critical)
2. MUST rules that are partial (high)
3. SHOULD rules that are non-conformant (medium)
4. SHOULD rules that are partial (low)

### 5. Remediation suggestions

For each gap, a concrete suggestion (file to modify, what to add). Keep suggestions minimal — the goal is the smallest change that achieves conformance, not a rewrite.

### 6. Overall assessment

One of:

- **Conformant** — all MUST rules satisfied, most SHOULD rules satisfied
- **Partially conformant** — all MUST rules satisfied, significant SHOULD gaps
- **Non-conformant** — one or more MUST rules not satisfied

---

## Intended use

- Run when onboarding a new service to verify observability baseline
- Run after the Observability Standard is updated to detect newly introduced gaps
- Run periodically (e.g. quarterly) across all services for ecosystem-wide conformance
- Run as part of a pre-deployment review for new services
- Pair with the [AGENTS.md Conformance Audit](AGENTS_CONFORMANCE_AUDIT.md) for full-stack governance checking
