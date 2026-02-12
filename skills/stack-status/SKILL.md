---
name: stack-status
description: Check Docker Compose service status on a remote host via SSH. Use when asked to check service health, uptime, or container status on a server.
---

# Stack Status

SSH into a target host and report the status of Docker Compose services.

## Run

- Run `scripts/stack_status.py --host <hostname> --compose-dir <path>` to check all services.
- Use `--services svc1 svc2` to check specific services only.

## Output

JSON to stdout: array of `{"name": "...", "status": "running|exited|...", "health": "...", "ports": "...", "uptime": "..."}` wrapped in `{"host": "...", "compose_dir": "...", "services": [...]}`.

## Notes

- Requires `ssh` in PATH.
- Assumes key-based or Tailscale SSH auth.
- Fails fast on SSH errors.
