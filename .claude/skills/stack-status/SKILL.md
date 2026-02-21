---
name: stack-status
description: Check Docker Compose service status on a remote host via SSH.
---

# Stack Status

Check Docker Compose service status on a remote host via SSH.

## Invocation

Call the `infra.stack_status` capability via MCP:

```
infra.stack_status(host="...", compose_dir="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | string | yes | — | SSH host target (e.g. user@hostname or an SSH config alias). |
| `compose_dir` | string | yes | — | Absolute path to the Docker Compose project directory on the remote host. |
| `services` | array? | no | — | List of service names to query. If null or empty, all services in the compose file are returned. |

## Error Codes

| Code | Description |
|------|-------------|
| `dependency_error` | ssh binary not found in PATH. |
| `ssh_error` | SSH connection or remote command execution failed. |

## Side Effects

Runs a read-only docker compose ps command on the remote host via SSH. No containers are started, stopped, or modified.
