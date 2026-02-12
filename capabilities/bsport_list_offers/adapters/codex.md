# Codex Adapter: bsport.list_offers

This adapter calls the existing `harmonytime-classes` skill as a thin CLI wrapper over the core capability.

## Invocation

Run the skill binary and pass inputs as flags. The output is JSON on stdout.

```
./skills/harmonytime_classes \
  --company 995 \
  --days 7 \
  --limit 50 \
  --activity yoga \
  --coach 123 \
  --available-only
```

## Input Mapping

- `company` -> `--company`
- `days` -> `--days`
- `limit` -> `--limit`
- `activity[]` -> repeat `--activity`
- `coach[]` -> repeat `--coach`
- `available_only` -> `--available-only`
- `raw` -> `--raw`

## Output Mapping

- stdout JSON maps directly to the capability output schema.
- Use `--pretty` for human-readable formatting (adapter-only concern).
