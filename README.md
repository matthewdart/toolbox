# toolbox

A personal toolbox of capabilities — deterministic, contract-driven plugins used by humans and agents to perform repeatable workflows.

---

## Purpose

Repeated workflows involving GitHub, infrastructure, and automation should not be re-implemented in prompts. Instead, they are encoded as capabilities with stable contracts, versioned, and callable from multiple surfaces (MCP, CLI, OpenAI tools).

---

## Repository Structure

```
toolbox/
├── capabilities/          All executable code (auto-discovered plugins)
├── core/                  Registry and CLI dispatch
├── adapters/              MCP server, OpenAI tool generation
├── .claude/skills/        Instructional skills (agent guidance, no code)
├── tests/                 Surface consistency and capability tests
├── docs/                  Operational guides and patterns
├── gpts/                  GPT configuration files
├── vendor/handbook/       Vendored governance handbook
├── .github/workflows/     Reusable GitHub Actions workflows
├── .mcp.json              MCP server config (auto-started by Claude Code)
├── AGENTS.md              Agent operating contract
├── CLAUDE.md              Claude Code quick-reference
└── README.md
```

---

## Capabilities

Each capability is a self-contained plugin under `capabilities/` with a JSON Schema contract, implementation, and metadata. The registry auto-discovers all plugins at import time.

Agents discover capabilities via the MCP server (configured in `.mcp.json`). The MCP server auto-starts when opening this repo in Claude Code.

### Usage

```bash
# Via CLI dispatch
python -m core.dispatch --capability text.normalize_markdown --input-json '{"text":"hello  world"}'

# Regenerate OpenAI adapter files from contracts
python -m adapters.openai.toolgen

# Run tests
pytest tests/
```

---

## Reusable GitHub Actions Workflows

### build-arm-image.yml

Build a Docker image for `linux/arm64` via QEMU cross-compilation and push to GHCR.

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `image_name` | yes | — | Image name (pushed as `ghcr.io/matthewdart/<image_name>`) |
| `dockerfile` | no | `Dockerfile` | Path to Dockerfile |
| `context` | no | `.` | Build context |
| `platforms` | no | `linux/arm64` | Target platform(s) |

```yaml
jobs:
  build:
    uses: matthewdart/toolbox/.github/workflows/build-arm-image.yml@main
    with:
      image_name: my-service
    secrets: inherit
```

### deploy-stack.yml

Deploy a Docker Compose stack to the Oracle Cloud VM via Tailscale SSH.

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `service_name` | yes | — | Service name — deploys to `/opt/<service_name>/` |
| `compose_file` | no | `docker-compose.yml` | Path to compose file in the calling repo |
| `vm_hostname` | no | `matthews-oracle-instance` | Tailscale hostname of the VM |
| `vm_user` | no | `ubuntu` | SSH user |

```yaml
jobs:
  deploy:
    uses: matthewdart/toolbox/.github/workflows/deploy-stack.yml@main
    with:
      service_name: my-service
    secrets: inherit
```

---

## Design Principles

1. **No sudo** — capabilities run as an unprivileged user
2. **User-space only** — no systemd, no package installs, no global filesystem mutation
3. **Deterministic** — same input produces the same output shape
4. **Fail fast** — missing prerequisites error clearly
5. **Explicit contracts** — inputs via schema, outputs validated

---

## License

Personal use. Adapt as needed.
