# Contracts

Contracts are the canonical, surface-agnostic definition of each capability.

## Contract Format (Canonical)

Contracts live in `capabilities/<plugin_dir>/contract.v1.json` and MUST include:

- `name`: capability id (e.g., `text.normalize_markdown`)
- `description`: short description
- `version`: version string (e.g., `v1`)
- `input_schema`: JSON Schema (draft-07) describing inputs
- `output_schema`: JSON Schema (draft-07) describing outputs
- `errors`: list of documented error codes and descriptions
- `side_effects`: optional string
- `version_notes`: optional string

Example:

```
{
  "name": "text.normalize_markdown",
  "description": "Normalize Markdown content",
  "version": "v1",
  "input_schema": { ... },
  "output_schema": { ... },
  "errors": [ ... ],
  "side_effects": "None"
}
```

## Validation Rules

- Inputs MUST be validated against `input_schema` before execution.
- Outputs MUST be validated against `output_schema` after execution.
- Any breaking behavior change requires a new contract version file.

## Versioning

- `v1 -> v1.1`: backward-compatible additions only.
- `v1 -> v2`: breaking changes.

Old versions remain available if adapters depend on them.
