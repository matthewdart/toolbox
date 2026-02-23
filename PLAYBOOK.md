# Playbook — Audits, Principles, and Agent Exploitation Model

This document is the operational reference for implementation, audits, and agent workflows in AI-assisted, model-centric systems. It is designed to be vendored into multiple repositories (via git subtree) and used consistently by humans and AI agents.

It sits within a four-document governance hierarchy:

- **[Manifesto](MANIFESTO.md)** — values, optimisation targets, and selection pressures (why)
- **[Tech Constitution](TECH_CONSTITUTION.md)** — minimum validity constraints (what must not break)
- **[Reference Architecture](REFERENCE_ARCHITECTURE.md)** — ecosystem defaults and expected fit (what it should look like)
- **Playbook (this document)** — implementation, audits, and agent behaviour (how)

---

## 0. How to Read and Use This Document

This playbook is structured into five layers. Each layer can be used independently, but together they form a complete system.

1. **Working & Agent Manifesto** — invariants and selection pressures (intent). See [MANIFESTO.md](MANIFESTO.md) for core values, optimisation target, outcomes, and anti-goals.
2. **Structural Principles** — non-opinionated implications of applying the manifesto
3. **Implementation Principles** — what is enforceable with current technology
4. **Audit Frameworks** — diagnostic enforcement
5. **Playbook Exploitation Model** — how this is used across repos and by agents

Nothing here is a product roadmap. This is a governance and leverage reference.

---

## 1. Aspirational Working & Agent Manifesto (Intent)

These principles define the long-term north star. They are portable across domains.

1. Expose, don't abstract away, underlying system capabilities
2. Ground all reasoning in canonical sources
3. Prefer mechanical derivation to authored duplication
4. Separate capability semantics from invocation mechanics
5. Default to headless determinism
6. Treat UI context as a signal surface, not an execution surface
7. Assume human–agent concurrency
8. Treat mismatches and uncertainty as assets
9. Produce reusable artifacts, not conversational residue
10. Optimize for orchestration, not autonomy

For the foundational values, optimisation target, core outcomes, and anti-goals that these principles operationalise, see [MANIFESTO.md](MANIFESTO.md).

---

## 2. Structural Principles Inferred from Practice (Non-Opinionated)

These are structural implications, not value judgements.

11. **Canonical models enable coordination**
    A shared, queryable model can act as a coordination surface across tools, agents, and humans.
12. **Projections are derived, not authoritative**
    Diagrams, matrices, reports, and views are projections that may be regenerated.
13. **Automation depends on stable identity**
    Persistent identifiers and referential continuity are prerequisites for long-lived automation.
14. **Read and write interactions are structurally distinct**
    Observation and mutation have different consequences and must be handled explicitly.
15. **Traceability can be generated rather than maintained**
    Relational views may be derived when the underlying model is consistent.

---

## 3. Pragmatic Implementation Principles

These approximate the manifesto under current technological constraints.

1. Canonical source anchoring must be explicit
2. Mechanical derivation is preferred; manual work requires justification
3. Headless-safe paths must exist
4. UI context must be observable, optional, and expiring
5. Examples are accelerators, not authorities
6. Drift must be visible
7. Artifacts must be regenerable or explicitly declared hand-authored

---

## 4. Tool Admission & Refactoring Discipline

### Tool Admission Checklist

A tool may move beyond experimental only if:

1. It removes concrete local friction immediately
2. Inputs and outputs are inspectable
3. It interoperates via existing primitives
4. It has a clear exit path
5. It occupies a defined role

### Refactoring Discipline

Refactoring is allowed only if it **reduces complexity** or **makes invariants more explicit**.

Refactors that merely reshuffle code, introduce abstractions, or align with generic "best practices" without clear payoff are considered regression.

Refactoring follows diagnosis — never precedes it.

#### Refactor Invariants

Before refactoring, the following must be made explicit and preserved:

- Authoritative domain concepts and semantics
- Pipeline boundaries and stage responsibilities
- Data ownership and direction of flow
- Accepted constraints and deliberate simplifications
- Dependency and tooling limits

If invariants are unclear, refactoring is premature.

#### Refactor Acceptance Criteria

A refactor must satisfy at least one of the following:

1. **Net complexity reduction** — fewer concepts, files, branches, or abstractions.
2. **Improved mental model alignment** — code structure maps more directly to domain understanding.
3. **Lower future change cost** — common changes become easier without increasing conceptual load.

If none apply, do not refactor.

#### Refactor Process

All non-trivial refactors follow a two-phase flow:

1. **Plan phase**
   - Describe proposed changes
   - State which complexity is reduced
   - List what will be deleted
   - Reaffirm preserved invariants

2. **Patch phase**
   - Implement exactly the approved plan
   - No additional abstractions or scope expansion

Skipping the plan phase is a red flag.

#### Explicit Constraints

During refactoring:

- Prefer deletion over addition
- Avoid new layers, frameworks, or configuration systems
- Avoid premature generalisation
- Keep modules and functions small and readable
- Maintain a single, explainable mental model

A refactor that cannot be explained in ~10 lines has failed.

#### Post-Refactor Coherence Check

Every refactor must be followed by:

- A short system description (≤10 lines)
- A list of public entry points and responsibilities
- A list of deleted code and removed concepts
- Confirmation that invariants still hold

If coherence has decreased, revert.

---

## 5. Audit Frameworks

Audits are diagnostic, not prescriptive. Evidence precedes change.

Audit outputs are stored in `reports/` with timestamped filenames.

### 5.1 Generic AI Slop Audit

Purpose: detect entropy, duplication, weak contracts, and low-signal abstractions.

Focus areas:

- Contracts and boundaries
- Error handling and failure modes
- Abstractions and layering
- Duplication and repetition

See [audits/AI_SLOP_AUDIT.md](audits/AI_SLOP_AUDIT.md) for the full prompt.

### 5.2 Agent Capability & Exposure Audit

Purpose: verify that underlying platform capabilities are exposed transparently and safely to agents.

Checks:

- Canonical source grounding
- Capability vs invocation separation
- Headless safety
- Provenance and regeneration

See [audits/AGENT_CAPABILITY_AUDIT.md](audits/AGENT_CAPABILITY_AUDIT.md) for the full prompt.

### 5.3 Ecosystem Acceptance Audit (e.g. Archi Maintainer)

Purpose: determine long-term ownership and acceptance viability within a specific ecosystem.

Outcome must be one of:

- Yes, largely as-is
- Yes, but only after specific changes
- No, not without fundamental re-scoping

See [audits/ARCHI_MAINTAINER_ACCEPTANCE_AUDIT.md](audits/ARCHI_MAINTAINER_ACCEPTANCE_AUDIT.md) for the full prompt.

### 5.4 Governance Consistency & Drift Audit

Purpose: audit governance documents as a system for inconsistencies, overlap, misclassification, or drift.

See [audits/GOVERNANCE_CONSISTENCY_AUDIT.md](audits/GOVERNANCE_CONSISTENCY_AUDIT.md) for the full prompt.

### 5.5 Workspace Hygiene Audit

Purpose: audit the state of all Git repositories across one or more development machines for uncommitted work, remote sync drift, stale branches, orphaned clones, and configuration inconsistencies.

Unlike the other audit prompts, this one is designed for both diagnosis and remediation — safe fixes are applied directly, while risky actions are flagged for human confirmation.

See [audits/WORKSPACE_HYGIENE_AUDIT.md](audits/WORKSPACE_HYGIENE_AUDIT.md) for the full prompt.

### 5.6 Observability Audit

Purpose: audit one or more service repositories against the [Observability Standard](OBSERVABILITY_STANDARD.md), verifying that health endpoints, startup logging, error output, request logging, and deployment verification conventions are implemented.

Produces a per-rule scorecard and prioritised gap analysis.

See [audits/OBSERVABILITY_AUDIT.md](audits/OBSERVABILITY_AUDIT.md) for the full prompt.

---

## 6. Playbook Exploitation Model (How Agents Use This)

### 6.1 Representation Layers

The following path conventions are illustrative defaults for consuming repositories. They are not requirements of this governance repo itself.

**Human-Readable Doctrine**

- `vendor/handbook/` — vendored governance artifacts (this repo)
- `docs/policies/` — project-specific policy documents

**Machine-Readable Contracts**

- `capabilities/*.yaml` — capability definitions
- Generated OpenAPI / schema subsets
- `vendor/` snapshots of canonical sources

**Run Artefacts (Evidence)**

- `reports/` — audit outputs (timestamped)
- `EXCEPTIONS.md` — recorded constitutional exceptions (see section 7)

### 6.2 Expected Agent Workflow Loop

1. Discover capabilities
2. Ground in canonical sources
3. Plan with explicit assumptions
4. Act minimally
5. Verify against canonical state
6. Record artefacts and evidence

### 6.3 Role-Oriented Agent Use

- **Auditor** — diagnose only
- **Mechaniser** — replace duplication with derivation
- **Integrator** — expose platform capabilities
- **Maintainer Reviewer** — apply ecosystem acceptance lens

Each role has explicit non-goals and produces concrete artefacts.

---

## 6.4 Per-Repo Agent Instructions (AGENTS.md)

AGENTS.md is the per-repo operationalisation of this handbook. Each repository maintains its own AGENTS.md that translates governance into concrete agent behaviour rules.

### Standard file roles

| File | Audience | Purpose |
|---|---|---|
| `AGENTS.md` | All AI agents | Agent behaviour rules and repo-specific constraints |
| `CLAUDE.md` | Claude Code | Imports AGENTS.md + preferences via `@` syntax, adds Claude-only notes |
| `CONTRIBUTING.md` | Human contributors | Bug reports, PRs, dev setup, testing |
| `.claude/agents/*.md` | Claude sub-agents | Specialised agent personas (e.g. code reviewer) |
| `vendor/handbook/OWNER_PREFERENCES.md` | All agents (via import) | Cross-repo conventions, patterns, and tool choices |

### Workflow tiers

Per-repo workflow rigour scales with pressure, consistent with the Manifesto principle "defer structure until pressure appears":

- **Tier 1 (lightweight, default):** Read context, state assumptions, propose, apply. For experimental, small, or single-purpose repos.
- **Tier 2 (structured):** Full Research / Convergence / Execution phases with mandatory Steps A-F (load context, interpret, impact analysis, resolve side effects, confirmation rules, apply). For repos with requirements, acceptance criteria, device safety, or stability contracts.

Repos may also use a **mode system** overlay (Prototype / Stabilised) where both tiers coexist, switchable per-task.

### Core principles (all tiers)

Regardless of tier, all repos enforce:

1. No silent scope expansion
2. Side effects must be surfaced (Tier 1: stated; Tier 2: resolved and documented)
3. Session capture in durable artefacts (chat is never authoritative)
4. Execution environment constraints (no sudo, user-space only, propose-first for risk)

### Naming conventions

| Name | Use |
|---|---|
| `AGENTS.md` | Agent behaviour rules (required, all repos) |
| `CLAUDE.md` | Claude-specific notes (required, all repos) |
| `docs/CONTRACT.md` or `SPEC.md` | Authoritative project specification |
| `CONTRIBUTING.md` | Human contributor guide |

Retired conventions: `CODEX_SPEC.md` (absorb into `AGENTS.md` or `docs/CONTRACT.md`).

### Templates

Canonical templates for all standard files live in `templates/` in this repository. See [templates/README.md](templates/README.md).

---

## 7. Exception Recording Convention

The [Tech Constitution](TECH_CONSTITUTION.md) requires that deliberate violations of its invariants be explicit, documented with rationale and scope, and include an exit or review condition (Invariant 6).

Each consuming repository SHOULD maintain an `EXCEPTIONS.md` file recording any constitutional exceptions. Each entry should include:

- **Invariant violated** — which constitutional invariant is affected
- **Scope** — what part of the system is covered by the exception
- **Rationale** — why the violation is necessary
- **Exit condition** — under what circumstances the exception should be revisited or removed
- **Date recorded** — when the exception was documented

If no exceptions exist, the file may be omitted or contain a statement confirming conformance.

---

## 8. Repository & Subtree Convention (Handbook Distribution)

This handbook is intended to live in a dedicated repository and be vendored into projects via git subtree at:

- `vendor/handbook/`

The handbook is treated as read-only in consuming repositories.

---

## 9. Living Status

This playbook is expected to evolve.

Revise it when:

- Friction accumulates
- Curiosity drops
- Tooling inertia appears
- Maintenance outweighs insight

When that happens, update the playbook — not just the tools.
