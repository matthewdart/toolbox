---
name: normalize-markdown
description: Normalize Markdown content with optional whitespace cleanup.
---

# Normalize Markdown

Normalize Markdown content with optional whitespace cleanup.

## Invocation

Call the `text.normalize_markdown` capability via MCP:

```
text.normalize_markdown(text="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | yes | — | Markdown text to normalize. |
| `options` | object | no | `{}` |  |

## Error Codes

| Code | Description |
|------|-------------|
| `validation_error` | Input did not match schema. |
| `output_validation_error` | Output did not match schema. |

## Side Effects

None.
