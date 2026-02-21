---
name: vm-bootstrap
description: Preflight check for VM deployment readiness. Connects via SSH and verifies Docker, Docker Compose, architecture, GHCR authentication, Tailscale, and per-service compose directory layout.
---

# Vm Bootstrap

Preflight check for VM deployment readiness. Connects via SSH and verifies Docker, Docker Compose, architecture, GHCR authentication, Tailscale, and per-service compose directory layout.

## Invocation

Call the `infra.vm_bootstrap` capability via MCP:

```
infra.vm_bootstrap(host="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | string | yes | — | SSH host target (e.g. user@hostname or an SSH config alias). |
| `compose_dirs` | array | no | `["/opt/remarkable-pipeline", "/opt/health-ledger", "/opt/archi-mcp-bridge"]` | Absolute paths to Docker Compose project directories on the remote host. |

## Error Codes

| Code | Description |
|------|-------------|
| `dependency_error` | ssh binary not found in PATH. |
| `ssh_error` | SSH connection failed for one or more checks. |

## Side Effects

Executes read-only commands on the remote host via SSH to verify deployment prerequisites. No state is modified.
