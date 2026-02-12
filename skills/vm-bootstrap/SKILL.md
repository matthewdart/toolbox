---
name: vm-bootstrap
description: Preflight check for VM deployment readiness. Use when asked to verify a server has Docker, GHCR auth, Tailscale, and required directories before deploying.
---

# VM Bootstrap

Verify (not install) that a remote VM has the required prerequisites for the MCP container stack.

## Run

- Run `scripts/vm_bootstrap.py --host <hostname>` to check all prerequisites.
- Use `--compose-dir <path>` to specify the compose directory (default: `/opt/mcp`).

## Checks

- Docker installed (>= 24.x)
- Docker Compose plugin available
- ARM architecture (`aarch64`)
- GHCR authentication (`docker login ghcr.io`)
- Tailscale running
- Compose directory exists with `docker-compose.yml`
- `.env` file present

## Output

JSON to stdout: `{"docker": "ok|missing", "compose": "ok|missing", "arch": "ok|unexpected", "ghcr": "ok|unauthenticated", "tailscale": "ok|missing", "compose_dir": "ok|missing", "env_file": "ok|missing"}`.

Remediation hints printed to stderr for any failures.

## Notes

- Requires `ssh` in PATH.
- Read-only: does NOT install or modify anything (no sudo).
- Assumes key-based or Tailscale SSH auth.
