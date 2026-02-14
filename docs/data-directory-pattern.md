# Data Directory Pattern — Operational Guide

Standard data directory layout for containerised services deployed to the VM.

Architectural pattern: [handbook REFERENCE_ARCHITECTURE.md §11.4](https://github.com/matthewdart/handbook/blob/main/REFERENCE_ARCHITECTURE.md#114-state--configuration)

---

## Host Layout

```
/opt/<service>/
  docker-compose.yml
  .env
  data/
    input/       # user-provided or externally sourced data
    output/      # generated, derived, or processed data
    workspace/   # runtime state, caches, temporary files
```

---

## Docker Compose Volume Mount

```yaml
volumes:
  - ./data:/app/data    # or ./data:/data depending on the service
```

---

## Conventions

- The **host directory** (`/opt/<service>/data/`) is the system of record for persistent state
- Use **bind mounts** (`./data`), not named Docker volumes — preserves inspectability and direct shell access
- `input/` is read-only from the service's perspective — user places data here before the service processes it
- `output/` and `workspace/` are written by the service
- Never store secrets in `data/` — use `.env` and environment variables
- The container treats its filesystem as ephemeral — anything not in `data/` is lost on container recreation

---

## Per-Service Examples

| Service | `input/` contents | `output/` contents | Mount path |
|---------|------------------|--------------------|------------|
| archi-mcp-bridge | `models/*.archimate` (ArchiMate model files) | — | `./data:/data` |
| health-ledger | `export.zip` (Apple Health export) | DuckDB database, parquet files, metadata | `./data:/app/data` |
| remarkable-pipeline | — (data fetched via SSH) | Rendered pages, OCR text, artefacts | `./data:/app/data` |

---

## First-Time Setup

When deploying a new service to the VM:

```bash
ssh matthews-oracle-instance
mkdir -p /opt/<service>/data/input /opt/<service>/data/output /opt/<service>/data/workspace
```

Then seed input data as required (e.g. copy a model file, upload an export).

---

## Inspection

```bash
# Check data directory contents
ssh matthews-oracle-instance "ls -la /opt/<service>/data/"

# Check disk usage
ssh matthews-oracle-instance "du -sh /opt/*/data/"
```
