---
name: survey-sessions
description: Survey and export Claude sessions across local CLI, web Claude Code, and claude.ai chat conversations.
---

# Survey Sessions

Survey and export Claude sessions across local CLI, web Claude Code, and claude.ai chat conversations.

## Invocation

Call the `claude.survey_sessions` capability via MCP:

```
claude.survey_sessions()
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sources` | array | no | `["cli", "code", "chat"]` | Which session sources to include: 'cli' (local .jsonl), 'code' (web Claude Code), 'chat' (claude.ai conversations). |
| `org_id` | string? | no | — | Claude organization UUID. Required for 'code' and 'chat' sources. Falls back to CLAUDE_ORG_ID env var. |
| `cookie` | string? | no | — | Browser cookie header for claude.ai auth. Required for 'code' and 'chat' sources. Falls back to CLAUDE_SESSION_COOKIE env var. |
| `status_filter` | string? | no | — | Filter web Code sessions by status. Only applies to 'code' source. Values: `active`, `idle`, `archived`. |
| `session_id` | string? | no | — | Filter to a specific session by ID (partial match supported). |
| `export` | boolean | no | `false` | If true, export full conversations as JSON files. |
| `export_dir` | string? | no | — | Directory to write exported conversations. Defaults to ~/.claude/exports/. |

## Error Codes

| Code | Description |
|------|-------------|
| `auth_required` | org_id and cookie are required for 'code' or 'chat' sources but were not provided. |
| `no_sessions_found` | No sessions matched the given filters. |

## Side Effects

Read-only. Reads local .jsonl files and makes HTTP GET requests to claude.ai APIs. Export mode writes JSON files to disk.
