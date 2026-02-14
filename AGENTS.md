# AGENTS.md — Toolbox

This document defines how AI coding agents (including Codex) should operate in this **Toolbox** repository.

The toolbox prioritises:

* lightweight, individual tools
* rapid prototyping and iteration
* gradual hardening into shared capabilities

Agents are collaborators. Humans remain accountable for decisions.

---

## Governance

This repository conforms to the [handbook governance hierarchy](vendor/handbook/README.md):

- [Manifesto](vendor/handbook/MANIFESTO.md) — values and selection pressures
- [Tech Constitution](vendor/handbook/TECH_CONSTITUTION.md) — validity invariants
- [Reference Architecture](vendor/handbook/REFERENCE_ARCHITECTURE.md) — ecosystem defaults and deployment model
- [Playbook](vendor/handbook/PLAYBOOK.md) — audits and agent exploitation model
- [Owner Preferences](vendor/handbook/OWNER_PREFERENCES.md) — cross-repo conventions, patterns, and tool choices
- [Infrastructure Map](vendor/handbook/INFRASTRUCTURE_MAP.md) — E2E architecture of all deployed components, Cloudflare tunnels, Docker containers, data flows, and VM state

This repo uses **Tier 1 + mode system** workflow (Prototype default, Stabilised for mature capabilities).

### Handbook version check

Before starting a session, verify the vendored handbook is current:

```
cat vendor/handbook/VERSION
```

If stale, note it to the user. Updates are pulled via:
`git subtree pull --prefix vendor/handbook https://github.com/matthewdart/handbook.git master --squash`

---

## Purpose

This repository contains a **capability-first toolbox**.

Agents assist with:

* implementing capabilities as self-contained plugins
* wiring adapters for OpenAI tools and MCP
* maintaining contracts and documentation

The repository explicitly supports **both exploratory and stabilised work**.

---

## Two Concepts

The toolbox has exactly two types of artefact:

### Capabilities

Executable code with JSON Schema contracts, auto-discovered by the registry, exposed via MCP.

* Live in `capabilities/<name>/`
* Discovered by agents via the MCP server (configured in `.mcp.json`, auto-started by Claude Code)
* Each has a contract, implementation, and plugin metadata

### Instructional Skills

Guidance-only SKILL.md files with no code behind them.

* Live in `.claude/skills/<name>/SKILL.md`
* Discovered natively by Claude Code
* Provide agent context and instructions beyond "call this tool"

---

## Operating Modes (Authoritative)

Agents MUST operate in one of the following modes. If not explicitly stated, **Prototype Mode is the default**.

### 1. Prototype Mode (Default)

Used for:

* experiments
* one-off or early-stage tools

Characteristics:

* speed over ceremony
* assumptions are allowed but must be stated
* contracts may be lightweight or provisional
* issues, plans, and ADRs are OPTIONAL

Breaking changes are allowed.

---

### 2. Stabilised Mode

Used for:

* shared or reused capabilities
* multi-surface tooling relied on by other tools
* anything claiming stability or reuse

Characteristics:

* explicit contracts
* versioning expectations
* documentation required
* side effects must be resolved and recorded

Breaking changes REQUIRE acknowledgement.

---

## Source of Truth

The following are authoritative, in descending order:

1. Explicit user instructions
2. This document (AGENTS.md)
3. Repository documentation
4. Capability contracts (`capabilities/*/contract.v1.json`)
5. Repository code

If authoritative sources do not exist, agents MAY infer and propose them.

---

## Core Principles (Always Apply)

1. **Capabilities before adapters**
   Capabilities are surface-agnostic. Adapters are thin.

2. **No silent scope expansion**
   New behaviour, assumptions, or side effects must be stated.

3. **Surface assumptions explicitly**
   Implicit context must become explicit inputs in capabilities.

4. **Prefer reuse over duplication**
   Temporary duplication is acceptable in Prototype Mode but must be resolved before stabilisation.

---

## Capability Lifecycle States

Capabilities may exist in one of the following states:

### Experimental

* minimal or informal contracts
* no stability guarantees

### Provisional

* canonical contract defined
* adapters exist for multiple surfaces
* minor breaking changes allowed

### Stable

* versioned contracts
* backward compatibility guaranteed
* full stabilised-mode rules apply

Agents should declare or infer the lifecycle state when modifying a capability.

---

## Capabilities and Plugins

Each capability is a **self-contained plugin** under `capabilities/<name>/` containing:

* `__init__.py` — plugin metadata (CAPABILITY_ID, ENTRY_POINT_MODULE, ENTRY_POINT_ATTR)
* `contract.v1.json` — canonical interface (JSON Schema draft-07)
* `implementation.py` — surface-agnostic logic
* `README.md` — documentation
* `adapters/` — surface-specific adapter files (optional)

Rules:

* If a capability exists, prefer using it over re-implementation
* The registry (`core/registry.py`) auto-discovers plugins — no manual wiring needed
* The MCP server (`adapters/mcp/server.py`) exposes all capabilities as tools

Agents SHOULD propose a new capability when:

* logic is reused
* behaviour must be deterministic
* multiple execution surfaces are needed

### Contract Format

Contracts live in `capabilities/<plugin_dir>/contract.v1.json` and MUST include:

* `name`: capability ID (e.g., `text.normalize_markdown`)
* `description`: short description
* `version`: version string (e.g., `v1`)
* `input_schema`: JSON Schema (draft-07) describing inputs
* `output_schema`: JSON Schema (draft-07) describing outputs
* `errors`: list of documented error codes and descriptions
* `side_effects`: optional string

### Naming Convention

```
<domain>.<verb>_<object>
```

Examples: `text.normalize_markdown`, `infra.deploy_compose`, `media.analyze_video`

### Contract Validation

* Inputs MUST be validated against `input_schema` before execution.
* Outputs MUST be validated against `output_schema` after execution.
* Any breaking behavior change requires a new contract version file.

### Contract Versioning

* `v1 -> v1.1`: backward-compatible additions only.
* `v1 -> v2`: breaking changes. Old versions remain available if adapters depend on them.

---

## Workflow Expectations

### Prototype Mode Workflow (Lightweight)

Agents SHOULD:

* analyse the request
* propose or infer capabilities
* state assumptions and trade-offs inline
* implement minimal working adapters

Agents MAY:

* skip GitHub issues
* skip formal plan docs
* iterate directly in code and docs

---

### Stabilised Mode Workflow (Structured)

Agents MUST:

* review relevant contracts and docs
* analyse impacts and side effects
* update documentation alongside code
* respect versioning and compatibility

Plans, ADRs, or issues SHOULD be created when decisions are long-lived.

---

## Execution Environments

### Codex Environments

Assume:

* no sudo
* no system services
* no package installation
* no inbound networking

All tooling must run in user space.

---

### User-Controlled Environments

If execution requires:

* sudo
* persistent services
* system modification

Agents MUST propose commands and effects first and wait for approval.

---

## Documentation and Session Capture

Prototype Mode:

* inline notes are sufficient

Stabilised Mode:

* decisions, assumptions, and impacts must be captured in durable artefacts

Chat history is never authoritative.

---

## Safe Defaults

* default to Prototype Mode
* default to minimal viable capability
* default to explicit assumptions
* default to later hardening, not upfront bureaucracy
* default to verifying results after every action — do not assume success
* default to active observation of running processes — review output, don't just wait

---

## Final Rule

Agents assist.
Humans decide.
Capabilities evolve.
