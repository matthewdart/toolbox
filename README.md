# Toolbox

A capability-first toolbox with shared core logic and thin adapters for:

- Codex skills
- OpenAI tool calling
- MCP (stdio)
- Local CLI

## Quickstart

### 1) Setup

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Generate OpenAI tool definitions

```
python -m adapters.openai.toolgen
```

### 3) Run a capability locally

```
python -m core.dispatch --capability text.normalize_markdown --input-json '{"text":"hello  \nworld"}'
```

### 4) Run MCP server (stdio)

```
python -m adapters.mcp.server
```

### 5) Run OpenAI tool runner

```
python -m adapters.openai.runner --message "Normalize this markdown: hello  \nworld"
```

Set `OPENAI_API_KEY` in your environment or `.env` (see `.env.example`).

## Currently Implemented

- `bsport.list_offers`
- `text.normalize_markdown`
- `harmonytime-classes` (Codex skill adapter)

See `CAPABILITIES.md` for full details and contracts.

## Docs

- `AGENTS.md` — agent rules
- `CAPABILITIES.md` — capability registry
- `CONTRACT.md` — contract format
- `docs/openai.md` — OpenAI runner
- `docs/mcp.md` — MCP server

## Tests

Run minimal tests with:

```
python -m unittest discover -s tests
```
