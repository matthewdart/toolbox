# Agent Capability & Exposure Audit — Prompt

## Purpose

This prompt is intended to be given to a coding agent to audit an existing codebase or system for how well it exposes underlying platform capabilities to agents transparently, safely, and in alignment with the governance framework.

The goal is diagnosis, not refactoring. The output should surface concrete gaps, risks, and high-leverage improvements.

---

## Prompt

You are working in an existing repository. Your task is to audit how the system exposes capabilities to agents (human or AI). You are evaluating whether agents can discover, understand, and safely use the system's capabilities without hidden coupling, undocumented state, or opaque invocation paths.

This is an ANALYSIS-ONLY task. Do not refactor code unless explicitly asked. Base all conclusions on evidence found in the repo.

## Scope & assumptions

- The system may be partially or fully agent-operated.
- Focus on structural exposure quality, not feature completeness.
- Prefer concrete evidence over speculation. If something is unclear, state it as unknown.

## What to inspect (mandatory)

### 1) Canonical source grounding

Assess whether the system's capabilities are grounded in explicit, canonical sources.

Look for:
- Are capabilities defined in versioned, inspectable artifacts (schemas, contracts, manifests)?
- Can an agent discover what the system does without reading implementation code?
- Are there capabilities that exist only in code with no corresponding contract or documentation?

### 2) Capability vs invocation separation

Assess whether the system separates *what it can do* from *how you ask it to do it*.

Look for:
- Are capabilities described independently of their transport (HTTP, CLI, SDK)?
- Can the same capability be invoked through multiple paths without semantic drift?
- Are there capabilities where the invocation mechanism leaks into the capability definition?

### 3) Headless safety

Assess whether all significant capabilities can be exercised without UI context.

Look for:
- Capabilities that require a browser, GUI, or interactive session
- State that is only accessible through UI interactions
- Operations that depend on transient UI context (session tokens, form state, cookies)

### 4) Provenance and regeneration

Assess whether agent actions and their outputs maintain provenance and can be regenerated.

Look for:
- Do agent outputs include references to their inputs and governing rules?
- Can derived artifacts be regenerated from canonical sources?
- Are there outputs that cannot be traced back to their inputs?

### 5) Discoverability and self-description

Assess whether the system is self-describing for agents.

Look for:
- OpenAPI, JSON Schema, or equivalent machine-readable contracts
- Capability manifests or registries
- Gaps where an agent would need to guess or infer capabilities

### 6) Error transparency

Assess whether errors are informative and actionable for agents.

Look for:
- Are error responses structured and typed?
- Can an agent distinguish between "bad request", "internal failure", and "not supported"?
- Are there silent failures or error responses that require human interpretation?

### 7) Boundary clarity for agents

Assess whether agents can determine the scope and limits of their operations.

Look for:
- Are read vs write operations clearly distinguished?
- Are destructive operations identifiable before invocation?
- Are there operations where the blast radius is ambiguous?

## Analysis to perform

For each category above:
- Identify concrete examples (file paths, endpoints, schemas, commands).
- Explain why this is a capability exposure risk.
- Assess severity: Low / Medium / High.

Then answer:
- Which capabilities are well-exposed and agent-ready?
- Which capabilities are hidden, implicit, or unsafe for agent use?
- What is the minimum change set to make the system safely agent-operable?

## Scoring rubric

For each major capability or subsystem, score 0-2 on:
1) Canonical grounding
2) Invocation independence
3) Headless safety
4) Provenance clarity
5) Discoverability

Highlight any area averaging ≤1.

## Output format

Produce a structured report with:

1. Scope and assumptions
2. Summary of overall agent-readiness (low / medium / high)
3. Findings by category (with evidence)
4. Capability exposure hotspots (ranked by risk)
5. High-leverage improvements (≤5)
6. What is already well-exposed and should not change

Be precise, conservative, and evidence-based. Prefer "unknown" over guessing.

---

## Intended use

- Run when onboarding agents to a new system
- Use as a pre-integration diagnostic before agent-facing API changes
- Use to evaluate whether a system meets the governance framework's agent operating assumptions
