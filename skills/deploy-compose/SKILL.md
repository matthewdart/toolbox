---
name: deploy-compose
description: Deploy Docker Compose services on a remote host via SSH. Use when asked to deploy, restart, or pull container images on a server.
---

# Deploy Compose

SSH into a target host and run `docker compose pull && docker compose up -d` for specified services (or all).

## Run

- Run `scripts/deploy_compose.py --host <hostname> --compose-dir <path>` to deploy all services.
- Use `--services svc1 svc2` to deploy specific services only.
- Use `--pull-only` to pull images without restarting.
- Use `--dry-run` to print the SSH command without executing.

## Output

JSON to stdout: `{"host": "...", "compose_dir": "...", "services": [...], "action": "deployed|pulled", "exit_code": 0}`

## Notes

- Requires `ssh` in PATH.
- Assumes key-based or Tailscale SSH auth (no password prompts).
- Fails fast on SSH or docker compose errors.
