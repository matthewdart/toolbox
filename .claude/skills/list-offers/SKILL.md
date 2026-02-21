---
name: list-offers
description: Fetch upcoming bsport offers for a company with optional filters.
---

# List Offers

Fetch upcoming bsport offers for a company with optional filters.

## Invocation

Call the `bsport.list_offers` capability via MCP:

```
bsport.list_offers()
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | integer | no | `995` | Bsport company id. |
| `days` | integer | no | `7` | Number of days ahead to include. 0 means no end date. |
| `limit` | integer | no | `50` | Maximum offers to return. 0 means no limit. |
| `activity` | array | no | `[]` | Case-insensitive substring filters for activity_name. |
| `coach` | array | no | `[]` | Coach id filters (matches coach or coach_override). |
| `available_only` | boolean | no | `false` | Only include offers where available=true. |
| `raw` | boolean | no | `false` | Return raw offer objects instead of the reduced schema. |

## Error Codes

| Code | Description |
|------|-------------|
| `dependency_error` | Missing curl binary. |
| `network_error` | Network or HTTP failures. |
| `invalid_response` | Invalid JSON response. |
| `validation_error` | Invalid input values. |
| `pagination_loop` | Pagination loop detected. |

## Side Effects

Network calls to the bsport offers API.
