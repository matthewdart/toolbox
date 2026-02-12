# AGENTS.md — Toolbox‑Optimised

This document defines how AI coding agents (including Codex) should operate in this **Toolbox** repository.

The toolbox prioritises:

* lightweight, individual tools
* rapid prototyping and iteration
* gradual hardening into shared capabilities

Agents are collaborators. Humans remain accountable for decisions.

---

## Purpose

This repository contains a **capability‑first toolbox**.

Agents assist with:

* analysing existing skills and capabilities
* discovering and extracting reusable capabilities
* implementing capabilities as self-contained plugins
* wiring adapters for Codex, OpenAI tools, and MCP

The repository explicitly supports **both exploratory and stabilised work**.

---

## Operating Modes (Authoritative)

Agents MUST operate in one of the following modes. If not explicitly stated, **Prototype Mode is the default**.

### 1. Prototype Mode (Default)

Used for:

* experiments
* skill‑to‑capability discovery
* one‑off or early‑stage tools

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
* multi‑surface tooling relied on by other tools
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
2. CONTRACT.md and declared authoritative documents
3. Repository documentation
4. Capability contracts (`capabilities/*/contract.v1.json`)
5. Repository code

If authoritative sources do not exist, agents MAY infer and propose them.

---

## Core Principles (Always Apply)

1. **Capabilities before adapters**
   Capabilities are surface‑agnostic. Adapters are thin.

2. **No silent scope expansion**
   New behaviour, assumptions, or side effects must be stated.

3. **Surface assumptions explicitly**
   Implicit context in skills must become explicit inputs in capabilities.

4. **Prefer reuse over duplication**
   Temporary duplication is acceptable in Prototype Mode but must be resolved before stabilisation.

---

## Capability Lifecycle States

Capabilities may exist in one of the following states:

### Experimental

* derived directly from skills
* minimal or informal contracts
* no stability guarantees

### Provisional

* canonical contract defined
* adapters exist for multiple surfaces
* minor breaking changes allowed

### Stable

* versioned contracts
* backward compatibility guaranteed
* full stabilised‑mode rules apply

Agents should declare or infer the lifecycle state when modifying a capability.

---

## Workflow Expectations

### Prototype Mode Workflow (Lightweight)

Agents SHOULD:

* analyse the skill or request
* propose or infer capabilities
* state assumptions and trade‑offs inline
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

Plans, ADRs, or issues SHOULD be created when decisions are long‑lived.

---

## Research, Convergence, Execution Phases

Agents must distinguish between:

### Research Phase

* explore alternatives
* surface assumptions
* avoid premature implementation

### Convergence Phase

* select and justify an approach
* identify rejected alternatives

### Execution Phase

* apply confirmed decisions
* minimise exploration

In Prototype Mode, phases may be combined if assumptions are documented.

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

### User‑Controlled Environments

If execution requires:

* sudo
* persistent services
* system modification

Agents MUST propose commands and effects first and wait for approval.

---

## Capabilities and Plugins

Each capability is a **self-contained plugin** under `capabilities/<name>/` containing:

* `contract.v1.json` — canonical interface
* `implementation.py` — surface-agnostic logic
* `__init__.py` — plugin metadata (CAPABILITY_ID, ENTRY_POINT_MODULE, ENTRY_POINT_ATTR)
* `README.md` — documentation
* `adapters/` — surface-specific adapter files

Rules:

* If a capability exists, prefer using it over re‑implementation
* Skills under `skills/` are thin CLI wrappers that delegate to capabilities
* The registry auto-discovers plugins — no manual wiring needed

Agents SHOULD propose a new capability when:

* logic is reused
* behaviour must be deterministic
* multiple execution surfaces are needed

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

---

## Final Rule

Agents assist.
Humans decide.
Capabilities evolve.
