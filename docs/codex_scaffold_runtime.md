# Meta-skill: scaffold_toolbox_python_runtime

Lightweight guide to scaffold the Python toolbox runtime.

## Purpose

- Ensure `/core`, `/contracts`, `/adapters`, and `/capabilities` are present.
- Create `core.dispatch` and contract-based validation.

## Expected Outputs

- `core/dispatch.py`
- `adapters/openai/toolgen.py`
- `adapters/mcp/server.py`
- `requirements.txt`

## Command Hints

- Use `python -m adapters.openai.toolgen` to generate OpenAI tools.
- Use `python -m core.dispatch --capability <id> --input-json '<json>'` for local runs.
