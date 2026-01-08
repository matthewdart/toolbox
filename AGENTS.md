# AGENTS.md

## Purpose

This repository contains a **Toolbox of reusable helpers ("capabilities")** designed to be callable through **multiple execution surfaces**:

* Codex skills
* OpenAI function / tool calling
* MCP servers
* CLI and/or HTTP adapters

Each capability is defined **once**, with a stable contract, and exposed via adapters.

---

## How to Work With This Repository (Agents)

### Golden Rules

1. **Capabilities are surface-agnostic**

   * Business logic MUST NOT be embedded directly in Codex prompts, MCP handlers, or OpenAI tool schemas.
   * Logic belongs in a shared implementation module.

2. **Every capability has a contract**

   * Inputs, outputs, side-effects, and failure modes must be explicit.
   * Contracts are authoritative.

3. **Adapters are thin**

   * Codex / OpenAI / MCP layers only:

     * validate inputs
     * translate formats
     * call the core capability
     * return results

4. **Backward compatibility matters**

   * Capabilities may evolve.
   * Contracts must be versioned if behavior changes.

---

## Repository Structure (Authoritative)

```
/capabilities/        # Capability definitions (what exists)
/contracts/           # Canonical contracts (schemas + semantics)
/core/                # Shared implementation logic
/adapters/
  ├─ codex/           # Codex skill wrappers
  ├─ openai/          # OpenAI function/tool definitions
  ├─ mcp/             # MCP server implementations
  ├─ cli/             # CLI adapters
/docs/
  ├─ AGENTS.md
  ├─ CAPABILITIES.md
  ├─ CONTRACT.md
```

---

## When Adding a New Capability

Agents MUST follow this sequence:

1. Define the capability in `/capabilities`
2. Define or update its contract in `/contracts`
3. Implement logic in `/core`
4. Add one or more adapters in `/adapters`
5. Update documentation

Skipping steps is not allowed.

---

## What Agents MUST NOT Do

* ❌ Hardcode logic inside Codex prompts
* ❌ Duplicate business logic across adapters
* ❌ Introduce surface-specific behavior into core logic
* ❌ Modify contracts without updating documentation

---

## Design Intent

This repository is intentionally designed to support:

* **future execution surfaces**
* **LLM orchestration**
* **tool composition**
* **capability discovery**

Agents should optimize for **clarity, composability, and reusability**, not speed of one-off execution.
