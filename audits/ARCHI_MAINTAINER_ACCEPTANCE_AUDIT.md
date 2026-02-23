# Archi Maintainer Acceptance Audit — Codex Prompt

## Purpose
This prompt is intended to be given to Codex (or another coding agent) to perform a **maintainer-grade architectural audit** of this repository.

It is focused exclusively on one governing question:

> **Would the maintainers of Archi reasonably accept this plugin as their own?**

This is a **diagnostic / judgment** prompt, not an execution or refactoring prompt.

---

## Canonical framing (non-negotiable)

Assume the following principles are true and must be used as the evaluation baseline:

1) This plugin is a **thin bridge over Archi/jArchi**, not a product.
2) Archi itself is the **system of record** for models, views, and semantics.
3) Anything added by this plugin must be:
   - clearly derived,
   - explicitly auxiliary or disposable,
   - impossible to confuse with core Archi concepts.
4) Design should reflect **long-term Archi maintainer expectations**, not experimental or fast-moving tooling.

When in doubt, prefer:
- smaller surface area
- fewer abstractions
- explicit invariants
- boring, predictable mechanisms

---

## Audit scope

Inspect the entire repository, with special attention to:
- HTTP API design and semantics
- DTOs and boundary typing
- persistence / filesystem usage
- error handling and error taxonomy
- OpenAPI schema and its relationship to code
- MCP / agent-facing surfaces
- naming, vocabulary, and implied ownership

Do **not** infer intent beyond what is present in code and docs.

---

## Core evaluation question

Answer this explicitly:

> *If this repository were submitted as a pull request to the official Archi project, would maintainers plausibly accept it as an Archi-owned plugin?*

Your answer MUST be one of:
- **Yes, largely as-is**
- **Yes, but only after specific changes**
- **No, not without a fundamental re-scoping**

You must justify the answer with concrete evidence.

---

## Analysis dimensions (mandatory)

### 0) Archi code conventions and Eclipse/RCP idioms
Assess whether the plugin would feel *native* to the Archi codebase and ecosystem.

Audit:
- Eclipse/RCP plugin posture (OSGi manifest, activation model, extension points, minimal runtime footprint)
- JDK / target compatibility with Archi’s supported runtime
- Naming and package structure relative to typical Archi plugins
- Logging and error hygiene (no unnecessary noise or internal leakage)
- Persistence conservatism (no new durable system of record)
- Testing posture (deterministic unit/contract tests + e2e as supplement)

For each divergence, classify it as:
- stylistic (low risk)
- maintainability-impacting (medium risk)
- ecosystem-incompatible (high risk)

---

### 1) Scope & authority discipline
Assess whether the plugin:
- introduces new domain concepts beyond Archi’s model
- creates new identities or lookup semantics that could be mistaken for Archi primitives
- accumulates state that looks persistent or authoritative

Explicitly call out scope creep or authority leakage.

---

### 2) Boundary clarity and contracts
Assess:
- how requests and responses are typed
- whether boundaries are explicit and strict
- whether contracts are enforced at the edge or deferred to runtime

---

### 3) Error semantics and recoverability
Assess:
- clarity and consistency of error categories
- distinction between protocol, execution, and internal failures
- actionability and stability of error codes

Judge whether Archi maintainers would be comfortable supporting this model long-term.

---

### 4) Persistence and filesystem usage
Assess:
- whether filesystem usage is clearly auxiliary
- whether stored data is versioned and validated
- whether corruption is handled loudly or silently

Explicitly answer:
> *Does this code accidentally introduce a new system of record?*

---

### 5) Abstractions, layering, and cohesion
Assess:
- class responsibilities
- presence of god-classes
- speculative or unused abstractions

Flag any abstraction that increases maintenance burden without enforcing invariants.

---

### 6) Naming and conceptual alignment
Assess whether naming:
- aligns with Archi concepts
- avoids parallel vocabularies
- clearly signals what is derived, temporary, or internal

Include API paths, DTOs, classes, and on-disk structures.

---

### 7) OpenAPI and external contract posture
Assess:
- whether OpenAPI reflects runtime behavior
- whether it is strict and deterministic enough for client codegen
- whether it is treated as an enforced contract or an aspirational document

---

## Required output format

Produce a structured report with:

1. **Executive summary** (≤10 lines)
2. **Would Archi accept this?** (explicit verdict)
3. **Key blockers to acceptance** (ranked, with evidence)
4. **What aligns well with Archi standards**
5. **What fundamentally does not**
6. **Minimal change set to reach acceptability** (≤5 items)
7. **What should explicitly remain out of scope**

Use concrete file paths, symbols, and behaviors as evidence.
State “unknown” explicitly where evidence is missing.

---

## Non-goals
- Do NOT refactor code
- Do NOT propose large redesigns unless required to answer the acceptance question
- Do NOT optimize for MCP/LLM convenience at the expense of Archi maintainability

This audit is about **maintainer trust**, not feature completeness.