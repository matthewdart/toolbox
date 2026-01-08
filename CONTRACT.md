# Contracts

A **contract** is the authoritative description of a capability’s interface and behavior. It is what allows the same capability to be exposed consistently across execution surfaces (Codex, OpenAI tools, MCP, CLI, HTTP).

Contracts must be:

- **Explicit**: inputs, outputs, side-effects, and failure modes are stated.
- **Stable**: compatible changes extend a contract; breaking changes require a new version.
- **Surface-agnostic**: no mention of Codex/MCP/OpenAI-specific shapes except in adapter docs.

## What a Contract Defines

- Inputs (schema + semantics)
- Outputs
- Side effects
- Error conditions
- Versioning rules

## Contract Format

Prefer **JSON Schema** for machine-validated inputs/outputs, with optional accompanying Markdown for additional semantics and examples.

Suggested path shape:

```
contracts/<capability>.v1.json
```

## What Every Contract Should Include

At minimum:

- **Name**: stable identifier (e.g. `canvas-markdown`)
- **Version**: `v1`, `v2`, … (increment on breaking changes)
- **Summary**: 1–2 sentences describing intent
- **Inputs**: types, required/optional, validation rules
- **Outputs**: types and where they are emitted (stdout/file/return value)
- **Side effects**: network calls, filesystem writes, external services
- **Dependencies**: required binaries, auth, env vars, permissions
- **Failure modes**: expected error cases and how they surface
- **Examples**: minimal, copy/paste runnable examples

## Versioning Guidelines

- **Patch** (doc-only): clarify wording, add examples; no behavior changes.
- **Minor** (compatible): add optional inputs, additional outputs, broader input acceptance.
- **Major** (breaking): remove/rename inputs, change output shape/semantics, change side effects.

Keep old versions available if adapters depend on them.

## Contract vs Adapter

| Concern | Contract | Adapter |
| --- | --- | --- |
| Input validation | ✅ | ⚠️ (light) |
| Semantics | ✅ | ❌ |
| Transport | ❌ | ✅ |
| Prompting | ❌ | ✅ |

## Where Contracts Live (Current State)

This repository is still early. For now, contracts for implemented capabilities are documented inline in `CAPABILITIES.md`.

As the toolbox grows, prefer moving contracts into a dedicated `contracts/` folder (one file per capability per version) and treating `CAPABILITIES.md` as an index.
