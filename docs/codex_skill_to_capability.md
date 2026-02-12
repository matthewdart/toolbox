# Skill → Capability Discovery Prompt

Use this prompt to decompose an existing skill into first-class capabilities and implement them across Codex, OpenAI tools, and MCP.

## Workflow

1. **Analyze the skill**
   - Identify distinct responsibilities (fetching, filtering, formatting, etc.).
2. **Propose capabilities**
   - Choose the minimal reusable set.
   - Use `<domain>.<verb>_<object>` naming.
3. **Define capabilities**
   - Create `/capabilities/<capability>.md` with description and non-goals.
4. **Author contracts**
   - Create `/contracts/<capability>.v1.json` with input/output schemas and errors.
5. **Implement core logic**
   - Place shared logic in `/core/<domain>/<capability>.py`.
6. **Wire adapters**
   - Codex: `/adapters/codex/<capability>.md`
   - OpenAI: generate tool JSON via `python -m adapters.openai.toolgen`
   - MCP: ensure `/adapters/mcp/server.py` picks up the contract
7. **Update registry**
   - Document in `CAPABILITIES.md`.

## Guardrails

- Adapters must be thin; no business logic.
- Contracts are authoritative and versioned.
- Surface implicit context as explicit inputs.
