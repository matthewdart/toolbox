# infra.bootstrap_vm

## Description

Preflight check for VM deployment readiness. Connects to a remote host via SSH and verifies that the essential infrastructure prerequisites are in place: Docker, Docker Compose, ARM64 architecture, GHCR authentication, Tailscale connectivity, and per-service compose directory layout.

## Checks performed

1. **docker** -- Docker engine is installed and accessible.
2. **compose** -- Docker Compose plugin is available.
3. **arch** -- Host architecture is ARM64.
4. **ghcr** -- Docker is authenticated to `ghcr.io`.
5. **tailscale** -- Tailscale is running and online.
6. **compose_dir:{service}** -- `docker-compose.yml` exists in each compose directory.
7. **env_file:{service}** -- `.env` file exists in each compose directory.

## Non-goals

- Modifying remote state or installing missing dependencies.
- Managing SSH keys or authentication.
- Orchestrating multi-host or multi-step deployments.

## Deterministic behavior

Given the same host and compose directories, the capability executes the same SSH command sequence. The outcome depends on remote state and is therefore not fully deterministic.
