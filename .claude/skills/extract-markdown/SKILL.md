---
name: extract-markdown
description: Extract markdown from a ChatGPT Canvas shared URL.
---

# Extract Markdown

Extract markdown from a ChatGPT Canvas shared URL.

## Invocation

Call the `chatgpt.extract_markdown` capability via MCP:

```
chatgpt.extract_markdown(url="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | yes | — | Canvas share URL. |
| `output` | string? | no | — | Where to write the extracted markdown. Use 'auto' for auto-named file, a directory path, or a file path. Null means no file output. |

## Error Codes

| Code | Description |
|------|-------------|
| `dependency_error` | Missing curl binary. |
| `network_error` | Network or HTTP failures fetching the canvas URL. |
| `parse_error` | Canvas page does not contain extractable markdown content. |
| `validation_error` | Input did not match schema. |

## Side Effects

Performs a network fetch of the shared canvas URL using curl. Optionally writes a local .md file.
