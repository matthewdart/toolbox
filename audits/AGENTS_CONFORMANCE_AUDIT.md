# AGENTS.md Conformance & Drift Audit Prompt

## Role

You are acting as a **documentation conformance auditor**.

Your task is to audit a repository's agent instruction files (AGENTS.md, CLAUDE.md, CONTRIBUTING.md) against the handbook governance hierarchy and templates.

Your goal is to detect **missing files, structural drift, stale vendoring, and conformance gaps**.

This is a **diagnostic audit**, not a rewrite exercise.

---

## 1. File Presence Check

Verify the following files exist in the repository root:

| File | Required | Purpose |
|---|---|---|
| `AGENTS.md` | Yes | Agent behaviour rules |
| `CLAUDE.md` | Yes | Claude-specific notes (must reference AGENTS.md) |
| `CONTRIBUTING.md` | Optional | Human contributor guide |
| `.claude/agents/*.md` | Optional | Sub-agent personas |

For each missing required file, flag as **MISSING (critical)**.

---

## 2. Handbook Vendoring Check

Check for the vendored handbook:

* Does `vendor/handbook/` exist?
* Does `vendor/handbook/VERSION` exist, and what version does it contain?
* What is the current upstream handbook version? (If accessible, compare against the handbook repo.)
* If the vendored version is behind upstream, flag as **STALE VENDOR** and note the version gap.
* If `vendor/handbook/` does not exist, check whether AGENTS.md references the handbook via URL instead. If neither, flag as **NOT VENDORED (critical)**.

---

## 3. AGENTS.md Structural Conformance

Check that AGENTS.md contains the following sections from the canonical template. For each section, classify as:

* **Present and conformant** — section exists and follows the template pattern
* **Present but divergent** — section exists but structure or content has drifted from the template
* **Missing** — section does not exist
* **N/A** — section is optional and correctly omitted (e.g. Operating Mode for single-tier repos)

### Required sections (must exist in all repos):

1. **Governance** — must reference the handbook hierarchy (vendored or via URL)
2. **Source of Truth** — must define an ordered hierarchy
3. **Non-Negotiable Rules** — must contain at least one repo-specific rule
4. **Workflow** — must declare a tier (Tier 1 or Tier 2) or operating mode
5. **Execution Environment** — must define sandboxed and user-controlled constraints
6. **Session Capture** — must state that chat is not authoritative
7. **Safe Defaults** — must include standard defaults
8. **Final Rule** — must include "Agents assist. Humans decide."

### Optional sections (present when applicable):

9. **Operating Mode** — for repos with Prototype/Stabilised modes
10. **Development Commands** — build/test/lint commands
11. **Architecture** — inline or pointer to docs/
12. **Conventions** — inline or pointer to docs/

For each required section that is missing, flag as **MISSING SECTION (high)**.
For divergent sections, quote the divergence and assess whether it is intentional or accidental.

---

## 4. CLAUDE.md Conformance

Verify that CLAUDE.md:

* References AGENTS.md (e.g. "Read AGENTS.md for full agent instructions")
* Does NOT duplicate content from AGENTS.md
* Contains only Claude-specific notes (or explicitly states "No additional notes")
* Is ≤ 30 lines (flag if substantially longer — may indicate content that belongs in AGENTS.md)

If CLAUDE.md duplicates AGENTS.md content, flag as **DUPLICATION (high)**.

---

## 5. Fixed Section Drift Check

The following sections contain content that should be consistent across all repos (FIXED in the template). Compare against the canonical template and flag any divergence:

### Execution Environment
Expected content (sandboxed): no sudo, no systemd, no package installation, no inbound networking.
Expected content (user-controlled): sudo requires confirmation, describe before executing, destructive actions never assumed safe.

### Session Capture
Expected: decisions captured in durable artefacts, chat not authoritative.

### Safe Defaults
Expected: minimal changes, propose-first, transparency, resolve side effects.

### Final Rule
Expected: "Agents assist. Humans decide." followed by repo-specific closing line.

For each divergence, classify as:
* **Intentional adaptation** — justified by repo-specific needs
* **Accidental drift** — likely copy-paste or editing artefact
* **Weakening** — the fixed section has been softened or diluted

---

## 6. Tier and Workflow Consistency

Check that the declared workflow tier matches the repo's actual structure:

* **Tier 1 repos** should NOT have Steps A-F, plan doc requirements, or ADR conventions (over-structured).
* **Tier 2 repos** should have Steps A-F or equivalent structured workflow, and should reference authoritative docs in Step A.
* **Mode system repos** should define both Prototype and Stabilised modes with clear switching criteria.

Flag mismatches between declared tier and actual workflow content.

---

## 7. Cross-Reference Check

Verify that:

* Source of Truth item #2 references a document that actually exists in the repo
* Architecture section points to a file that exists (if it references docs/ARCHITECTURE.md)
* Conventions section points to a file that exists (if it references docs/CONVENTIONS.md)
* Any CONTRACT.md, SPEC.md, or requirements/ referenced actually exist

Flag broken references as **BROKEN REFERENCE (high)**.

---

## 8. Output Format (Strict)

Produce the audit in the following structure:

1. **Executive Summary** (≤5 lines)
2. **File Presence** (table: file, status, notes)
3. **Handbook Vendoring** (version, staleness, status)
4. **Structural Conformance** (table: section, status, notes)
5. **CLAUDE.md Status** (conformant / divergent / missing)
6. **Fixed Section Drift** (list of divergences with classification)
7. **Tier/Workflow Consistency** (declared vs actual)
8. **Broken References** (list)
9. **Overall Assessment** — one of:
   * Conformant, no drift
   * Conformant, minor drift (list items)
   * Non-conformant, requires intervention (list critical items)

Evidence first. Interpretation second. Recommendations only if explicitly requested.

---

## Intended Use

* Run when onboarding a new repo to verify initial setup
* Run periodically (e.g. quarterly or after handbook version bumps) to detect drift
* Run before major refactors to confirm documentation is current
* Pair with the Governance Consistency Audit for full-stack governance checking
