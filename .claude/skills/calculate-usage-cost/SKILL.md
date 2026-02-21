---
name: calculate-usage-cost
description: Summarize OpenAI usage from a JSONL log and optionally calculate estimated costs using user-supplied pricing.
---

# Calculate Usage Cost

Summarize OpenAI usage from a JSONL log and optionally calculate estimated costs using user-supplied pricing.

## Invocation

Call the `openai.calculate_usage_cost` capability via MCP:

```
openai.calculate_usage_cost(usage_log_path="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `usage_log_path` | string | yes | — | Path to a JSONL usage log (e.g., produced by media.analyze_video with log_usage=true). |
| `pricing` | object? | no | — | Optional pricing table. If omitted, returns usage totals without cost fields. |
| `fail_on_unknown_model` | boolean | no | `true` | If pricing is provided, error when a model is missing from the price table. |

## Error Codes

| Code | Description |
|------|-------------|
| `validation_error` | Input did not match schema. |
| `output_validation_error` | Output did not match schema. |
| `capability_error` | Usage log was unreadable or pricing was missing. |

## Side Effects

Reads a local JSONL file; no network calls.
