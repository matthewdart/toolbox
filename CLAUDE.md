# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Commands

```bash
# Run tests
pytest tests/

# Regenerate all OpenAI adapter files from contracts
python -m adapters.openai.toolgen
```

## Gotchas

- Capability imports are **lazy** — missing deps won't error until runtime.
- `gh` CLI must be pre-authenticated — capabilities never prompt for credentials.
- New capabilities follow `<domain>.<verb>_<object>` naming (e.g. `text.normalize_markdown`).
- Plugin `__init__.py` must export `CAPABILITY_ID`, `ENTRY_POINT_MODULE`, `ENTRY_POINT_ATTR`.
- The contract (`contract.v1.json`) is the single source of truth. OpenAI adapters are generated from it, the MCP server reads it at runtime. Regenerate adapters after contract changes.
- Capabilities are discovered by agents via MCP (configured in `.mcp.json`). Instructional skills live in `.claude/skills/`.
