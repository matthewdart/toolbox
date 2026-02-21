---
name: deploy-compose
description: Deploy Docker Compose services on a remote host via SSH.
---

# Deploy Compose

Deploy Docker Compose services on a remote host via SSH.

## Invocation

Call the `infra.deploy_compose` capability via MCP:

```
infra.deploy_compose(host="...", compose_dir="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | string | yes | — | SSH host target (e.g. user@hostname or an SSH config alias). |
| `compose_dir` | string | yes | — | Absolute path to the Docker Compose project directory on the remote host. |
| `services` | array? | no | — | List of service names to deploy. If null or empty, all services in the compose file are targeted. |
| `pull_only` | boolean | no | `false` | If true, only pull images without starting services. |
| `dry_run` | boolean | no | `false` | If true, return the SSH command that would be executed without running it. |

## Error Codes

| Code | Description |
|------|-------------|
| `dependency_error` | ssh binary not found in PATH. |
| `ssh_error` | SSH connection or remote command execution failed. |

## Side Effects

Pulls Docker images and optionally starts containers on the remote host via SSH.
