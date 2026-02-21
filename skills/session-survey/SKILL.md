# session-survey

Survey and consolidate the status of all Claude sessions — local CLI sessions, web Claude Code sessions, and regular claude.ai chat conversations.

## Usage

```bash
# Local CLI sessions only
python3 scripts/session-survey.py --local-only

# All sessions (requires browser cookie for web)
python3 scripts/session-survey.py \
  --org-id "$CLAUDE_ORG_ID" \
  --cookie "$CLAUDE_SESSION_COOKIE"

# Filter web Code sessions by status
python3 scripts/session-survey.py --status idle --org-id ... --cookie ...

# Only chat conversations
python3 scripts/session-survey.py --chat-only \
  --org-id "$CLAUDE_ORG_ID" --cookie "$CLAUDE_SESSION_COOKIE"

# Only web Code sessions (no chat, no CLI)
python3 scripts/session-survey.py --web-only \
  --org-id "$CLAUDE_ORG_ID" --cookie "$CLAUDE_SESSION_COOKIE"
```

## Three session sources

### Local CLI sessions
Parses `.jsonl` files in `~/.claude/projects/*/` to extract session metadata: title (first user message), branch, timestamps, message count, size.

### Web Claude Code sessions
Calls `GET https://claude.ai/v1/sessions` with the `anthropic-beta: ccr-byoc-2025-07-29` header and cookie auth. Returns sessions with `session_status` (active/idle/archived), model, repo, branch.

### Chat conversations
Calls `GET /api/organizations/{orgId}/chat_conversations` with cookie auth. Returns all regular claude.ai conversations with title, model, timestamps, and auto-generated summaries. Full message history is available via the detail endpoint.

## Exporting conversations

```bash
# Export all local CLI sessions
python3 scripts/session-survey.py --local-only --export

# Export a specific session by ID (partial match)
python3 scripts/session-survey.py --local-only --export --session-id abc123

# Export web Code sessions to a custom directory
python3 scripts/session-survey.py --web-only --export --export-dir ./my-exports \
  --org-id "$CLAUDE_ORG_ID" --cookie "$CLAUDE_SESSION_COOKIE"

# Export only chat conversations
python3 scripts/session-survey.py --chat-only --export \
  --org-id "$CLAUDE_ORG_ID" --cookie "$CLAUDE_SESSION_COOKIE"

# Export only active Code sessions
python3 scripts/session-survey.py --web-only --export --status active \
  --org-id "$CLAUDE_ORG_ID" --cookie "$CLAUDE_SESSION_COOKIE"
```

Exports are written as individual JSON files to `~/.claude/exports/` (default). Each file contains:
- Session metadata (title, branch, repo, timestamps, model)
- Full conversation as a normalized message array (`role`, `text`, `tool_uses`, `timestamp`)
- For Code sessions: result summary with cost, turns, duration, and token usage
- For chat conversations: auto-generated summary from claude.ai

### Exported conversation format

Each message in the `conversation` array has:
- `role`: `"user"`, `"assistant"`, or `"tool_result"`
- `text`: The message content
- `tool_uses`: (assistant only) Array of tool calls with `tool`, `id`, `input_preview`
- `tool_use_id`, `output_preview`, `is_error`: (tool_result only) Tool execution results
- `timestamp`, `id`: Provenance

## Output
- **Survey mode** (default): Human-readable report to stderr, full JSON array to stdout
- **Export mode** (`--export`): One JSON file per session to the export directory

## Authentication for web sessions and chat
Both the Code sessions and chat conversations APIs use cookie-based auth (same as your browser session). To get the cookie:
1. Open `claude.ai/code` in your browser
2. Open DevTools > Application > Cookies > `claude.ai`
3. Copy all cookies as a header string (or at minimum the session cookies)
4. Pass via `--cookie` or `CLAUDE_SESSION_COOKIE` env var

Your org ID is visible in the URL when logged into claude.ai, or via the `/api/account` endpoint.
