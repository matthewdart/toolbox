# Codebase Architecture Audit — Prompt

## Purpose

This prompt is intended to be given to a coding agent to perform a deep architectural and design audit of an existing codebase. It proceeds through six sequential stages — discovery, best-practice research, current-state audit, ideal target architecture, gap analysis, and executive summary — producing a comprehensive, evidence-based assessment.

The goal is diagnosis, not refactoring. The output should surface every meaningful deviation from best practice, design an achievable target architecture, and produce a prioritised remediation roadmap.

This audit is substantially more thorough than the other audit prompts in this collection. It is designed for repositories that warrant a full architectural review, not routine checks. Expect it to consume significant context and time.

---

## Prompt

You are performing a deep architectural and design audit of this codebase. Work through the following six stages sequentially. Be thorough, opinionated, and specific — reference actual files, functions, and line numbers. Do not be gentle; this audit should surface every meaningful deviation from best practice.

This is an ANALYSIS-ONLY task. Do not refactor code, fix bugs, or implement changes unless explicitly asked. Base all conclusions on evidence found in the repo and on researched best practices for the specific stack.

## Scope & assumptions

- The codebase may use any language, framework, or architectural style. Do not assume a stack — discover it.
- Focus on structural quality, architectural fitness, security posture, and long-term maintainability.
- Prefer concrete evidence over speculation. If something is unclear, state it as unknown.
- Read files thoroughly — do not skim. Open and inspect actual source files, not just configs.
- When in doubt, dig deeper. Check git history for patterns if useful.
- Every claim must be backed by evidence from the codebase or a cited external source.
- Use Mermaid diagrams where they aid understanding (dependency maps, component diagrams, data flows, Gantt charts).

---

## 1. Discovery & Inventory

Systematically explore the entire codebase and document:

- **Languages & versions** — check config files, lock files, runtime targets
- **Frameworks & libraries** — with versions, distinguishing core dependencies from dev/build tooling
- **Architecture style** — monolith, microservices, modular monolith, serverless, etc.
- **Project structure** — directory layout, module boundaries, entry points
- **Build & deployment** — CI/CD pipelines, Dockerfiles, IaC, scripts
- **Data layer** — databases, ORMs, migration strategies, caching
- **External integrations** — APIs consumed/exposed, message queues, third-party services
- **Testing infrastructure** — frameworks, coverage tooling, test organisation
- **Configuration & secrets management**
- **Documentation** — existing docs, API specs, ADRs

Produce a structured inventory with a dependency map (Mermaid) showing how major components relate.

---

## 2. Best Practice Research

Based on the specific stack discovered in Stage 1, research and document the current consensus best practices. For each major technology/framework found, document:

- Official recommended project structure and patterns
- Established design patterns for that ecosystem (e.g. repository pattern, clean architecture layers, composition patterns, error handling idioms)
- Security best practices specific to the stack
- Performance best practices and known anti-patterns
- Testing strategies recommended by the community (unit/integration/e2e split, mocking approaches)
- Dependency management conventions
- Observability & logging standards

Cite sources with URLs. Prioritise official documentation, widely-respected style guides (e.g. Google, Airbnb, framework authors), and recent conference talks or RFCs.

---

## 3. Current State Audit

Audit the actual codebase against general software engineering principles AND the stack-specific best practices from Stage 2. Organise findings by severity: **Critical / Major / Minor / Informational**.

For each finding:

| Field | Description |
|---|---|
| **ID** | Unique identifier (e.g. AUD-001) |
| **Severity** | Critical / Major / Minor / Informational |
| **Category** | Architecture, Security, Performance, Maintainability, Testing, DX |
| **Location** | File paths and line numbers |
| **Description** | What the issue is |
| **Evidence** | Code snippets or structural observations |
| **Impact** | What could go wrong, what cost this imposes |

Cover at minimum:

- Separation of concerns and layer violations
- Coupling and cohesion analysis
- Error handling consistency and completeness
- Security vulnerabilities (injection, auth, secrets exposure, dependency CVEs)
- Performance bottlenecks and anti-patterns
- Code duplication and DRY violations
- Naming conventions and consistency
- Test coverage gaps and test quality
- Dead code and unused dependencies
- Configuration and environment handling
- API design quality (if applicable)
- Database query patterns and potential N+1s or missing indexes (if applicable)

---

## 4. Ideal Target Architecture

Based on what this codebase is trying to do (its domain and purpose), design the ideal architecture as if starting from scratch with the same stack. This is the north star — ambitious but realistic. Document:

- **Architectural vision** — which architectural style and why
- **Module/package structure** — with a directory tree
- **Component diagram** (Mermaid) — all major components and their relationships
- **Data flow diagrams** (Mermaid) — for the key workflows
- **Layer definitions** — clear responsibilities and allowed dependencies (dependency rule)
- **Key design patterns** — what to adopt and where they apply
- **API design standards** — naming, versioning, error contracts
- **Error handling strategy**
- **Testing strategy** — test pyramid, what to test at each level, target coverage
- **Security architecture** — auth flows, input validation strategy, secrets management
- **Observability strategy** — structured logging, metrics, tracing
- **CI/CD pipeline design**
- **Naming conventions and code style standards**

Include concrete examples showing what key modules/files would look like under this ideal design.

---

## 5. Gap Analysis & Remediation Roadmap

Compare the current state (Stage 3) against the ideal architecture (Stage 4). For each gap:

| Field | Description |
|---|---|
| **Gap ID** | Unique identifier (e.g. GAP-001), cross-referencing relevant AUD-* IDs |
| **Current state** | What exists today |
| **Target state** | What the ideal looks like |
| **Effort** | S / M / L / XL |
| **Risk of change** | Low / Medium / High — will this break things? |
| **Priority** | P1–P4, considering impact x effort x risk |
| **Implementation approach** | Step-by-step, with migration strategies for breaking changes |
| **Dependencies** | Other GAP-* IDs that must be completed first |

Then produce:

- A **prioritised remediation roadmap** grouped into phases: Quick Wins → Foundation → Enhancement → Polish
- A **Mermaid Gantt chart** showing the suggested sequencing
- **Migration risk notes** for any changes that require careful rollout

---

## 6. Executive Summary

Produce a concise executive summary that:

- Summarises the overall health of the codebase with a letter grade (A–F) across each audit category (Architecture, Security, Performance, Maintainability, Testing, DX)
- Highlights the top 5 most critical findings
- Presents the remediation roadmap at a glance
- Estimates total technical debt cost in relative terms
- Calls out what the codebase does well (be fair)

---

## Scoring rubric

For each major module or subsystem, score 0–2 on:

1. Architectural fitness (separation of concerns, layer discipline)
2. Security posture (input validation, secrets handling, dependency hygiene)
3. Performance (no obvious anti-patterns, appropriate caching/indexing)
4. Maintainability (naming, duplication, cohesion)
5. Test quality (coverage, assertion strength, failure-mode testing)
6. Developer experience (build speed, documentation, onboarding friction)

Highlight any area averaging ≤ 1.

---

## Output format

Produce a structured report covering all six stages. Each stage should be clearly delineated with a heading. The report should be self-contained and readable without access to the codebase.

If the report is large, it may be split into separate sections — but the structure above defines the canonical ordering. Each section must cross-reference the others (e.g. Gap Analysis references AUD-* IDs from the Current State Audit).

---

## Intended use

- Run when onboarding to an unfamiliar codebase to build a comprehensive understanding
- Run before a major refactor or re-architecture to establish a baseline and target
- Run periodically (e.g. annually) as a deep health check on mature repositories
- Run when evaluating whether to invest in, acquire, or inherit a codebase
- Use the executive summary for stakeholder communication; use the detailed stages for engineering planning

This prompt can be followed up with: "Implement the Quick Wins phase from the remediation roadmap" to begin acting on findings.
