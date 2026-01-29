# Capabilities

This file is the registry (index) of capabilities currently implemented in this repository.

> Note: some capabilities still have Codex skill adapters under `skills/`. Core implementations live in `/core`, with thin adapters in `/adapters` (see `AGENTS.md`).

This repo currently ships implemented capabilities and skills, with core capabilities exposed via Codex, OpenAI tools, and MCP where applicable.

## Implemented

| Capability | Status | Surfaces | Description |
| --- | --- | --- | --- |
| `canvas-markdown` | implemented | Codex skill, CLI | Extract markdown from a ChatGPT Canvas shared URL |
| `create-private-gist` | implemented | Codex skill, CLI | Create a secret GitHub Gist from files or stdin via `gh` |
| `bsport.list_offers` | implemented | Codex, OpenAI, MCP, CLI | Fetch upcoming bsport offers with filters |
| `media.analyze_video` | implemented | OpenAI, MCP, CLI | Transcribe a video and extract key slides using OpenAI APIs |
| `openai.calculate_usage_cost` | implemented | OpenAI, MCP, CLI | Summarize OpenAI usage logs and estimate costs with user-supplied pricing |
| `text.normalize_markdown` | implemented | Codex, OpenAI, MCP, CLI | Normalize Markdown text via deterministic whitespace rules |
| `harmonytime-classes` | adapter | Codex skill, CLI | Thin wrapper over `bsport.list_offers` for Harmony Time (company 995) |

---

## `canvas-markdown`

Extract embedded markdown from a shared ChatGPT Canvas page.

- **Skill**: `skills/canvas-markdown/SKILL.md`
- **Implementation**: `skills/canvas-markdown/scripts/canvas_markdown.py`
- **CLI entrypoint (convenience)**: `skills/canvas_markdown`
- **Packaged skill artifact**: `skills/canvas-markdown.skill` (zip; don’t edit directly)

### Contract (v1)

**Inputs**

- `url` (string): Canvas share URL, provided as a CLI arg; if omitted, read from `stdin` (trimmed).
- `-o/--output` (optional string): Where to write the extracted markdown.
  - If omitted: write markdown to `stdout`.
  - If `"auto"`: write to `<slugified-title>.md` in the current working directory.
  - If a directory path: write to `<dir>/<slugified-title>.md`.
  - If a file path: write to that file path.
- `--print-filename` (flag): When used with `--output`, print the resolved output path; otherwise print the suggested filename.

**Outputs**

- By default: writes extracted markdown to `stdout`.
- When `--output` is provided: writes extracted markdown to a file; optionally prints the path when `--print-filename` is set.

**Side effects**

- Performs a network fetch of the shared canvas URL using `curl`.
- Optionally writes a local `.md` file.

**Dependencies**

- `python3`
- `curl` available in `PATH`
- Network access to fetch the canvas page

**Failure modes (non-exhaustive)**

- Missing URL (no arg and empty stdin).
- `curl` missing from `PATH`.
- Network/HTTP failure (surfaced from `curl -fsSL`).
- The fetched HTML doesn’t contain an extractable canvas `content` payload.
- `--output` points to a non-existent directory when specified as a directory (or ends with `/`).
- File write errors (permissions, invalid path, etc.).

**Examples**

- Print markdown: `./skills/canvas_markdown "<url>"`
- Write to a suggested filename in CWD: `./skills/canvas_markdown "<url>" -o auto`
- Write to a directory: `./skills/canvas_markdown "<url>" -o ./out/ --print-filename`

---

## `create-private-gist`

Create a **secret** GitHub gist from one or more files, or from stdin.

- **Skill**: `skills/create-private-gist/SKILL.md`
- **Implementation**: `skills/create-private-gist/scripts/create_private_gist.py`
- **CLI entrypoint (convenience)**: `skills/create_private_gist`
- **Packaged skill artifact**: `skills/create-private-gist.skill` (zip; don’t edit directly)

### Contract (v1)

**Inputs**

- `files` (0+ paths): When provided, create a gist from these files.
- stdin (string): Used when no `files` are provided.
- `-d/--desc` (optional string): Gist description.
- `-f/--filename` (optional string): Filename to use for stdin mode only.

**Outputs**

- Writes `gh gist create` output to `stdout` (typically the created gist URL), and exits `0` on success.

**Side effects**

- Creates a new secret gist under the authenticated `gh` user.

**Dependencies**

- `python3`
- `gh` available in `PATH` and authenticated (`gh auth login`)

**Failure modes (non-exhaustive)**

- `gh` missing from `PATH`.
- `--filename` provided together with file arguments.
- `'-'` included in file arguments (stdin cannot be mixed with files).
- Empty stdin when no files are provided.
- `gh gist create` failure (auth, API error, invalid file path, etc.).

**Examples**

- Create gist from files: `./skills/create_private_gist README.md CAPABILITIES.md`
- Create gist from stdin: `cat README.md | ./skills/create_private_gist -f README.md -d "toolbox readme"`

---

## `bsport.list_offers`

Fetch upcoming offers for a bsport company with optional filters.

- **Contract**: `contracts/bsport.list_offers.v1.json`
- **Core**: `core/bsport/list_offers.py`
- **Adapters**:
  - Codex: `adapters/codex/bsport.list_offers.md` (via `skills/harmonytime_classes`)
  - OpenAI: `adapters/openai/bsport.list_offers.json`
  - MCP: `adapters/mcp/server.py` (registered from contracts)

### CLI usage (via Codex skill adapter)

- Fetch next 7 days: `./skills/harmonytime_classes`
- Only available offers, limit 10: `./skills/harmonytime_classes --available-only --limit 10`
- Filter by activity substring: `./skills/harmonytime_classes --activity yoga --activity pilates`
- Include raw offers: `./skills/harmonytime_classes --raw --pretty`

---

## `text.normalize_markdown`

Normalize Markdown text using deterministic whitespace rules.

- **Contract**: `contracts/text.normalize_markdown.v1.json`
- **Core**: `core/text/normalize_markdown.py`
- **Adapters**:
  - Codex: `adapters/codex/capability_wrapper.md`
  - OpenAI: `adapters/openai/text.normalize_markdown.json`
  - MCP: `adapters/mcp/server.py` (registered from contracts)

### CLI usage

```bash
python -m core.dispatch --capability text.normalize_markdown --input-json '{"text":"hello  \\nworld"}'
```

---

## `media.analyze_video`

Transcribe a local video file and extract key slide images using OpenAI APIs.

- **Contract**: `contracts/media.analyze_video.v1.json`
- **Core**: `core/media/analyze_video.py`
- **Adapters**:
  - OpenAI: `adapters/openai/media.analyze_video.json` (generated from contracts)
  - MCP: `adapters/mcp/server.py` (registered from contracts)

### CLI usage

```bash
python -m core.dispatch --capability media.analyze_video --input-json '{"video_path":"/tmp/example.mp4"}'
```

Outputs are written to `./<video_stem>_analysis/` by default.

---

## `openai.calculate_usage_cost`

Summarize OpenAI usage from a JSONL log and optionally calculate estimated costs using a user-supplied pricing table.

- **Contract**: `contracts/openai.calculate_usage_cost.v1.json`
- **Core**: `core/openai/calculate_usage_cost.py`
- **Adapters**:
  - OpenAI: `adapters/openai/openai.calculate_usage_cost.json` (generated from contracts)
  - MCP: `adapters/mcp/server.py` (registered from contracts)

### CLI usage

```bash
python -m core.dispatch --capability openai.calculate_usage_cost --input-json '{"usage_log_path":"/path/to/openai_usage.jsonl"}'
```

---

## `harmonytime-classes` (Codex skill adapter)

Thin CLI wrapper around `bsport.list_offers` with Harmony Time defaults.

- **Skill**: `skills/harmonytime-classes/SKILL.md`
- **Implementation**: `skills/harmonytime-classes/scripts/harmonytime_classes.py`
- **CLI entrypoint (convenience)**: `skills/harmonytime_classes`
- **Packaged skill artifact**: `skills/harmonytime-classes.skill` (zip; don’t edit directly)

This adapter preserves the existing CLI flags and defaults while delegating all logic to `core/bsport/list_offers.py`.

---

## Naming (preferred for future core capabilities)

When adding new capabilities intended for multi-surface adapters, prefer stable IDs shaped like:

```
<domain>.<verb>_<object>
```

Examples:

- `text.extract_metadata`
- `files.embed_images`
- `archimate.sync_model`
