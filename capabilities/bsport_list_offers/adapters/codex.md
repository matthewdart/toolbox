# Codex Adapter: bsport.list_offers

This adapter calls the capability via CLI dispatch.

## Invocation

```
python -m core.dispatch --capability bsport.list_offers --input-json '{
  "company": 995,
  "days": 7,
  "limit": 50,
  "activity": ["yoga"],
  "coach": [123],
  "available_only": true
}'
```

## Input Mapping

- `company` -> integer, required
- `days` -> integer
- `limit` -> integer
- `activity` -> array of strings
- `coach` -> array of integers
- `available_only` -> boolean
- `raw` -> boolean

## Output Mapping

- stdout JSON maps directly to the capability output schema.
