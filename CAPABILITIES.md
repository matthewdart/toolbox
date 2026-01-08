# Capabilities

This file is the registry (index) of capabilities currently implemented in this repository.

> Note: today these capabilities live as **Codex skills** and **CLI scripts** under `skills/`. The long-term goal is to extract shared core implementations and keep adapters thin (see `AGENTS.md`).

This repo currently ships **two implemented capabilities**, both exposed as **Codex skills** and runnable as **local CLI scripts**.

## Implemented

| Capability | Status | Surfaces | Description |
| --- | --- | --- | --- |
| `canvas-markdown` | implemented | Codex skill, CLI | Extract markdown from a ChatGPT Canvas shared URL |
| `create-private-gist` | implemented | Codex skill, CLI | Create a secret GitHub Gist from files or stdin via `gh` |

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

## Naming (preferred for future core capabilities)

When adding new capabilities intended for multi-surface adapters, prefer stable IDs shaped like:

```
<domain>.<verb>_<object>
```

Examples:

- `text.extract_metadata`
- `files.embed_images`
- `archimate.sync_model`
