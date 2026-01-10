# Meta-skill: generate_openai_tool_from_contract

Generate OpenAI tool JSON files from contracts.

## Command

```
python -m adapters.openai.toolgen
```

## Expected Output

- One JSON file per contract in `adapters/openai/`, named `<capability>.json`.
- Idempotent regeneration (safe to re-run).
