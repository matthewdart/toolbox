---
name: push-ghcr
description: Build a Docker image for linux/arm64 and push to GitHub Container Registry. Use when asked to build, push, or publish a Docker image to GHCR.
---

# GHCR Push

Build and push a Docker image to `ghcr.io/matthewdart/<name>`.

## Quick Reference

The `github.push_ghcr` capability handles this programmatically via the MCP server. For manual or CI use:

```bash
docker buildx build --platform linux/arm64 -f Dockerfile -t ghcr.io/matthewdart/<name>:latest --push .
```

## Prerequisites

- `docker` with buildx plugin installed
- Authenticated to GHCR: `echo $GHCR_TOKEN | docker login ghcr.io -u matthewdart --password-stdin`
- QEMU registered for cross-platform builds: `docker run --rm --privileged multiarch/qemu-user-static --reset -p yes`

## Conventions

- Default platform: `linux/arm64` (Oracle Cloud VM target)
- Image naming: `ghcr.io/matthewdart/<repo-name>`
- Default tag: `latest` (additional tags via `--tag`)
- Dockerfile expected at repo root unless specified

## CI/CD

The toolbox provides a reusable GitHub Actions workflow at `.github/workflows/build-arm-image.yml`:

```yaml
jobs:
  build:
    uses: matthewdart/toolbox/.github/workflows/build-arm-image.yml@main
    with:
      image_name: my-service
    secrets: inherit
```
