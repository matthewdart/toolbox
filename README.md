# Toolbox

A capability-first toolbox with self-contained plugins and thin adapters for:

- OpenAI tool calling
- MCP (stdio)
- Codex skills
- Local CLI

## Architecture

Each capability is a **self-contained plugin** under `capabilities/`:

```
capabilities/
  text_normalize_markdown/
    contract.v1.json     # canonical interface definition
    implementation.py    # surface-agnostic logic
    README.md            # capability documentation
    adapters/
      openai.json        # OpenAI tool definition
      codex.md           # Codex adapter docs
```

Shared infrastructure in `core/` auto-discovers plugins and provides dispatch + validation. Adapters in `adapters/` translate capabilities for each surface.

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

## Capabilities

| Capability | Description |
| --- | --- |
| `bsport.list_offers` | Fetch upcoming bsport offers with filters |
| `text.normalize_markdown` | Normalize markdown via whitespace rules |
| `media.analyze_video` | Transcribe video + extract key slides (OpenAI) |
| `media.download_video` | Download video from URL via yt-dlp |
| `openai.calculate_usage_cost` | Summarize OpenAI usage logs + estimate costs |
| `canvas.extract_markdown` | Extract markdown from ChatGPT Canvas URLs |
| `gist.create_private` | Create secret GitHub Gists |

See `CAPABILITIES.md` for full details.

### Adding a new capability

1. Create `capabilities/<name>/` with `contract.v1.json`, `implementation.py`, `__init__.py`, and `README.md`
2. The registry auto-discovers it — no manual wiring needed
3. Run `python -m adapters.openai.toolgen` to generate the OpenAI adapter

## Docs

- `AGENTS.md` — agent rules
- `CAPABILITIES.md` — capability registry
- `CONTRACT.md` — contract format
- `docs/openai.md` — OpenAI runner
- `docs/mcp.md` — MCP server

## Tests

```
python -m unittest discover -s tests
```
