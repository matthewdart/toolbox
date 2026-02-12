---
name: ghcr-push
description: Build a Docker image for linux/arm64 and push to GitHub Container Registry. Use when asked to build and push a container image to GHCR.
---

# GHCR Push

Build a Docker image for a specified platform and push it to GitHub Container Registry.

## Run

- Run `scripts/ghcr_push.py --repo <owner/name> --context <path>` to build and push.
- Use `--dockerfile <path>` to specify a non-default Dockerfile.
- Use `--platform <platform>` to change target (default: `linux/arm64`).
- Use `--tag <tag>` to add tags (repeatable; default: `latest`).

## Output

JSON to stdout: `{"image": "ghcr.io/<repo>", "tags": [...], "platform": "..."}`.

## Notes

- Requires `docker` in PATH with buildx support.
- Requires GHCR authentication (via `docker login ghcr.io` or `GHCR_TOKEN` env var).
- Does NOT handle secrets; caller provides them via environment.
