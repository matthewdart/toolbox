# AI Slop Audit — Prompt

## Purpose

This prompt is intended to be given to a coding agent to audit an existing codebase for "AI slop": entropy-increasing, weakly grounded, low-signal code that looks plausible but degrades long-term maintainability, correctness, and evolvability.

The goal is diagnosis, not refactoring. The output should surface concrete risks, evidence, and high-leverage remediation areas.

---

## Prompt

You are working in an existing repository. Your task is to audit the codebase for signs of "AI slop": code and configuration that adds surface area without proportionate gains in correctness, clarity, or testability.

This is an ANALYSIS-ONLY task. Do not refactor code unless explicitly asked. Base all conclusions on evidence found in the repo.

## Scope & assumptions
- The codebase may contain human-written and AI-assisted code; do NOT attempt to attribute authorship.
- Focus on structural quality, invariants, and long-term maintainability.
- Prefer concrete evidence over speculation. If something is unclear, state it as unknown.

## What to inspect (mandatory)

### 1) Contracts and boundaries
Inspect all major boundaries:
- HTTP / API surfaces (OpenAPI, controllers, handlers)
- CLI interfaces
- File formats, schemas, migrations
- External integrations

Look for:
- Inconsistent representations of the same concept
- Vague or weakly typed schemas
- Missing or inconsistent validation

### 2) Error handling and failure modes
Inspect how the system handles:
- Invalid input
- Partial failures (IO, network, filesystem)
- Timeouts, retries, cancellation

Look for:
- Collapsed error categories
- Silent failures or overly broad exception handling
- Inconsistent error shapes or status codes

### 3) Abstractions and layering
Inspect:
- Utility layers, helpers, managers, services, adapters
- Interfaces and indirection layers

Look for:
- Abstractions with fan-in = 1 and fan-out = 1
- Pass-through wrappers
- Architecture that exists without a clear pressure or invariant

### 4) Duplication and repetition
Inspect:
- Repeated logic with superficial variation
- Copy-paste handlers or config blocks

Look for:
- Near-duplicate code
- Missed opportunities for data-driven structure

### 5) Configuration and option sprawl
Inspect:
- Config files
- Optional parameters and mode flags

Look for:
- Options that are never used
- Speculative generality (features for hypothetical futures)
- Defaults that hide important behavior

### 6) Types, schemas, and nullability
Inspect:
- Use of `any`, untyped maps, raw JSON
- Inconsistent null handling

Look for:
- Weak typing at boundaries
- Runtime-only contracts

### 7) Tests and verification
Inspect:
- Unit, integration, and contract tests

Look for:
- Tests that assert trivialities
- Snapshot tests with high churn
- Missing tests for invariants and failure modes

### 8) Documentation quality
Inspect:
- README, inline comments, docs

Look for:
- Verbose but non-operational prose
- Lack of decision records
- Mismatch between docs and code reality

### 9) Dependencies and tooling
Inspect:
- Direct and transitive dependencies

Look for:
- Overlapping libraries
- Dependencies introduced for trivial functionality
- Sudden growth in dependency graph

### 10) Local idioms and consistency
Inspect:
- Coding style, async model, naming, layering

Look for:
- Patterns inconsistent with the rest of the repo
- Imported idioms from other ecosystems

## Analysis to perform

For each category above:
- Identify concrete examples (file paths, symbols, endpoints).
- Explain why this is a slop signal (entropy, drift, weak invariants, etc.).
- Assess severity: Low / Medium / High.

Then answer:
- Where is entropy increasing fastest?
- Which parts of the system require non-local reasoning to change safely?
- Which abstractions could be removed with minimal behavior loss?

## Scoring rubric
For each major module or subsystem, score 0-2 on:
1) Contract clarity
2) Failure-mode completeness
3) Duplication
4) Cohesion
5) Test signal

Highlight any area averaging ≤1.

## Output format
Produce a structured report with:

1. Scope and assumptions
2. Summary of overall slop risk (low / medium / high)
3. Findings by category (with evidence)
4. Slop hotspots (ranked)
5. High-leverage remediation themes (≤5)
6. What NOT to change yet (areas that look noisy but are acceptable)

Be precise, conservative, and evidence-based. Prefer "unknown" over guessing.

---

## Intended use

- Run periodically as a health check on fast-moving repos
- Use as a pre-refactor diagnostic
- Use as a PR-level or milestone audit when AI assistance is heavy

If needed, this prompt can be paired with a follow-up prompt: "Implement only the top 3 remediation themes identified above."
