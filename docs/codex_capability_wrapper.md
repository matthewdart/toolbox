# Codex Capability Wrapper (Template)

Use this template to wrap a capability call in a thin, non-interactive script.

## Inputs

- JSON input (string or file) that matches the capability contract input schema.

## Command Template

```
python -m core.dispatch --capability <capability_id> --input-json '<json>'
```

Example:

```
python -m core.dispatch --capability text.normalize_markdown --input-json '{"text":"hello  \nworld"}'
```

## Output

- JSON response containing:
  - `ok`: boolean
  - `result` (on success) or `error` (on failure)

## Notes

- Do not embed business logic in the wrapper.
- Always validate inputs against the contract before calling.
