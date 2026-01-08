# Toolbox

A multi-surface **capability toolbox** for building reusable helpers that can be invoked via:

* Codex skills
* OpenAI function / tool calling
* MCP servers
* CLI / HTTP

## Why This Exists

Most AI tooling today is:

* tightly coupled to one execution surface
* prompt-centric
* hard to reuse or compose

This toolbox enforces a **capability-first architecture**:

> Define once → Call everywhere

---

## Core Principles

* Capability ≠ Adapter
* Contracts are explicit and stable
* Logic is shared, not duplicated
* Adapters are thin and replaceable

---

## Typical Use Cases

* Reusing the same helper in Codex and MCP
* Gradually migrating Codex skills to OpenAI tools
* Enabling agent-to-agent calls via MCP
* Building CLI tooling backed by AI-ready capabilities

---

## Currently Implemented

See `CAPABILITIES.md` for the canonical list, contracts, and usage.

* `canvas-markdown`
* `create-private-gist`

---

## Start Here

* `AGENTS.md` – rules for agents and Codex
* `CAPABILITIES.md` – what helpers exist
* `CONTRACT.md` – how contracts are defined
