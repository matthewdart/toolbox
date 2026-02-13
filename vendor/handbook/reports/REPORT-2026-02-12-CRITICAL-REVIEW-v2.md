# Critical Review v2 — Playbook Repository (Post-Remediation)

Generated: 2026-02-12

## Executive Summary

This is a follow-up review of the playbook repository after remediation of the issues identified in the first critical review and the prior governance consistency audit (2026-01-27).

The repository has improved substantially. All high-severity issues from the prior review have been resolved:

- PLAYBOOK.md is now valid Markdown with proper headings, lists, and rules
- REFERENCE_ARCHITECTURE.md no longer contains duplicate sections; numbering is clean (1-12)
- The governance feedback loop has closed — prior audit findings have been actioned
- Phantom file references are now explicitly marked as illustrative conventions
- Content duplication between Manifesto and Playbook has been eliminated
- Force-level language has been corrected (MUST promoted to Constitution or softened to SHOULD)
- The Constitution has been strengthened with Invariant 7 (Secrets Exclusion) and an extended Invariant 3

**Current assessment: Coherent, low drift risk.**

Remaining issues are minor and relate to residual overlap, scope questions, and the staleness of the prior audit report.

---

## File-by-File Review

---

### 1. README.md

**Status: Substantially improved.**

The README now includes the governance hierarchy, linked index for all documents/audits/reports, and a concrete `git subtree` example.

**Remaining issues:**

- **Minor: The "What this is" section could mention the hierarchy inline** rather than relying on a separate section. A reader skimming the bullets gets "Markdown and plain text only" but doesn't learn the force-level structure until the next section. Not a problem, just a density observation.

**Severity:** None actionable.

---

### 2. VERSION

**Content:** `0.1.0`

**Remaining issues:**

- **No versioning policy or changelog.** Same as prior review. What constitutes a version bump for a doctrine repository? This will matter when downstream consumers pin to a version via `git subtree`.

**Severity:** Low. Acceptable at 0.1.0 but worth defining before 0.2.0.

---

### 3. MANIFESTO.md

**Status: Improved.**

Refactoring procedures have been moved to the Playbook. The Manifesto now retains only the principle ("Refactoring is allowed only if it reduces complexity or makes invariants more explicit") and links to the Playbook for the full process. This correctly respects the force hierarchy.

**Remaining issues:**

- **Residual overlap: tool admission checklist.** The checklist appears in both MANIFESTO.md (lines 104-114, five items with qualifiers like "easily inspectable" and "not a vague promise") and PLAYBOOK.md (lines 80-88, five items with slightly different wording). The Manifesto version is the original with more nuance; the Playbook version is a thinner operational restatement. This is mild duplication — not the same severity as before, since the Manifesto version is the conceptual framing and the Playbook version is the operational checklist. But it is a future drift vector.

- **"Personal tooling stance" heading (line 69) still blurs force level.** The word "Personal" suggests individual preference, while the content reads as portable architectural principles. This was noted in the prior review and remains unchanged. It's a tone issue, not a structural one.

- **"Role-based tooling map" (lines 129-138) still has no concrete tools assigned.** Six role categories, no tools. This is a skeleton. It either needs populating or a note explaining that tools are listed in the Reference Architecture's section 9 and mapped to roles there.

**Severity:** Low. The document now respects its force level. The remaining items are polish.

---

### 4. PLAYBOOK.md

**Status: Substantially improved.**

The document is now valid Markdown with proper `#`/`##` headings, `-` list markers, and `---` horizontal rules. The authority claim has been corrected to "operational reference." Duplicated content (optimisation target, core outcomes, anti-goals, observed patterns) has been replaced with links to the Manifesto. The refactoring discipline has been absorbed here in full detail. Phantom file references are explicitly marked as illustrative. An exception recording convention (section 7) and governance consistency audit (section 5.4) have been added. All four audit prompts are now referenced with links to their files.

**Remaining issues:**

- **Minor: The "five layers" structure in section 0 is slightly awkward after the content changes.** Layer 1 is described as "Working & Agent Manifesto — invariants and selection pressures (intent)" but the Playbook's section 1 contains only the 10 aspirational principles, with a link to the Manifesto for the rest. The layer description implies more content than exists in this document for that layer. This is a cosmetic mismatch, not a contradiction.

- **Minor: Section numbering starts at 0.** The "How to Read" section is numbered 0, then content sections are 1-9. This is unconventional but not wrong. It does mean the five-layer structure described in section 0 doesn't map neatly to section numbers (layers 1-5 don't correspond to sections 1-5).

**Severity:** None actionable. The document is now fit for purpose.

---

### 5. TECH_CONSTITUTION.md

**Status: Strengthened.**

Now contains seven invariants (up from six). Invariant 3 (Bounded State Ownership) has been extended to explicitly cover ephemeral execution environments. Invariant 7 (Secrets Exclusion) is new and consolidates secrets constraints that were previously misclassified as defaults in the Reference Architecture.

**Remaining issues:**

- **Minor: "where feasible" qualifier in Invariant 1** remains the only soft language. Same observation as prior review — the qualifier is probably necessary but creates a loophole. Not changed, not a problem.

- **The exception recording convention is now operationalised** in PLAYBOOK.md section 7. This was a gap in the prior review and has been closed.

**Severity:** None. This remains the strongest document in the repository and is now stronger than before.

---

### 6. REFERENCE_ARCHITECTURE.md

**Status: Substantially improved.**

Duplicate section 5.2 has been removed. The two containerisation sections have been merged into a single section 11. Section numbering is now clean (1-12). Cross-references to other documents now use Markdown links. Force-level language has been corrected: genuine validity constraints are now explicitly attributed to the Constitution with links, while ecosystem defaults use SHOULD. The secrets section now distinguishes "Constitutional Constraints" from "Operational Expectation" and "Known Gap."

**Remaining issues:**

- **Vendor-specific tool names remain.** Section 9 still names Tailscale, Cloudflare, Apple Shortcuts, Obsidian, reMarkable, GitHub, and OpenAI. Each has an exit path. This was noted in the prior review as low severity and remains the same. The exit paths are adequate mitigation, but the density of named tools in a vendorable governance document is unusual.

- **The Reference Architecture's section 8 (Secrets) still uses MUST language** — but it now explicitly labels these as "Constitutional Constraints" from the Tech Constitution (Invariant 7) and links to it. The MUST language is correct here because it's quoting the Constitution, not asserting its own force level. This is properly resolved.

- **Section 11.1 uses the same "Constitutional Constraints" labeling pattern** for container-related invariants. This is also correct — it explicitly cites Invariant 3 and Invariant 2. The remaining container/networking defaults properly use SHOULD.

**Severity:** None actionable. The force-level problem has been resolved. Vendor tool density is a known, mitigated characteristic.

---

### 7. reports/REPORT-2026-01-27T222916Z.md

**Status: Improved (moved, renamed).**

Now lives in `reports/` with a consistent `.md` extension. Listed in the README index.

**Remaining issues:**

- **The report's findings are now stale.** The report references line numbers and quotes from the pre-remediation state of the documents. For example, it cites `PLAYBOOK.md:3` as "single consolidated reference" — this has been changed. It cites `REFERENCE_ARCHITECTURE.md:293` as "Services MUST NOT..." — this is now SHOULD NOT. It flags the duplicate section 5.2 — this has been removed. The report's "Overall Assessment: Coherent, moderate drift risk" no longer accurately reflects the repository state.

  This is expected — audit reports are point-in-time artifacts. But consumers encountering this report might be confused by findings that no longer apply. A brief annotation at the top noting "This report reflects the repository state as of 2026-01-27; most findings have since been addressed" would help.

**Severity:** Low. The report is historical and should be treated as such.

---

### 8. reports/REPORT-2026-02-12-CRITICAL-REVIEW.md

**Status: Historical.**

This is the first critical review (this review's predecessor). Same staleness consideration applies — its findings have been remediated. Should be treated as a historical artifact.

**Severity:** None.

---

### 9. audits/AI_SLOP_AUDIT.md

**Status: Fixed.**

Unicode artifacts (`⸻`, `•`, tab-indented lists) have been replaced with standard Markdown. The "Codex" branding has been removed from the title and body — now refers generically to "a coding agent."

**Remaining issues:** None.

**Severity:** None. Fit for purpose.

---

### 10. audits/AGENT_CAPABILITY_AUDIT.md

**Status: New.**

This file fills the gap identified in both the prior audit report and the first critical review. It provides a concrete audit prompt for evaluating how systems expose capabilities to agents.

The prompt covers seven inspection areas (canonical source grounding, capability vs invocation separation, headless safety, provenance, discoverability, error transparency, boundary clarity). It follows the same structure as the other audit prompts (purpose, prompt, scope, inspection areas, scoring, output format, intended use).

**Remaining issues:**

- **Minor: No "Deviation Guidance" or sensitivity to ecosystem context.** The other audit prompts (AI Slop, Archi Maintainer) acknowledge that context matters. This prompt is somewhat absolute in its expectations. An agent running this against a UI-first application might produce unhelpful findings. A brief scope/limitations note could help.

**Severity:** None actionable. The prompt is solid and fills a real gap.

---

### 11. audits/GOVERNANCE_CONSISTENCY_AUDIT.md

**Status: Unchanged. Still fit for purpose.**

**Severity:** None.

---

### 12. audits/ARCHI_MAINTAINER_ACCEPTANCE_AUDIT.md

**Status: Unchanged.**

**Remaining issues:**

- **Still references "Codex" in the title and body.** The AI Slop Audit was updated to use generic "coding agent" language, but this file still says "Codex Prompt" in the title and "given to Codex (or another coding agent)" in the body. Minor inconsistency across audit prompts.

- **Domain-specific in a general governance repo.** Same observation as prior review. The Archi-specific audit is well-written but its presence in a general governance repo is a scope question.

**Severity:** Low.

---

### 13. superseded/README.md

**Status: Unchanged. Acceptable placeholder.**

**Severity:** None.

---

## Cross-Cutting Issues

### A. Prior self-contradiction resolved

The prior review identified five specific cases where the repository violated its own principles. Current status:

| Principle | Prior Violation | Status |
|---|---|---|
| One canonical representation per concept | Duplicated content across Manifesto and Playbook | **Fixed** — Playbook references Manifesto |
| Mechanical derivation over manual duplication | Copy-paste sections in Reference Architecture | **Fixed** — duplicates removed |
| Files as primary coordination medium | PLAYBOOK.md not valid Markdown | **Fixed** — proper Markdown throughout |
| Drift must be visible | Hidden drift in duplicate sections | **Fixed** — single sections, clean numbering |
| Audits are diagnostic; evidence precedes change | Audit findings unactioned | **Fixed** — all major findings addressed |

### B. Governance feedback loop is now closed

The most damaging finding in the prior review was that the audit loop was open — problems were detected but not fixed. This has been resolved. The repository now demonstrates a complete cycle: audit → findings → remediation → re-review.

### C. Residual minor overlap

The tool admission checklist still appears in both MANIFESTO.md and PLAYBOOK.md with slightly different wording. This is the only remaining content duplication. It's defensible as "the Manifesto defines the principle, the Playbook operationalises it" — but the items are similar enough that they could drift.

### D. Stale historical reports

Both reports in `reports/` now describe a state of the repository that no longer exists. This is normal for audit artifacts, but a brief staleness annotation would help downstream consumers.

### E. No ownership or contribution model

Still no description of who maintains the canonical copy, how changes are proposed, or what the release discipline is. Same as prior review. This is a gap that matters more as the repo matures.

---

## Summary of Findings by Severity

### High
- None.

### Medium
- None.

### Low
- Tool admission checklist residual overlap between Manifesto and Playbook
- No versioning policy or changelog
- Vendor-specific tool names in a vendorable governance document (mitigated by exit paths)
- Stale historical reports should be annotated
- No ownership or contribution model
- Archi-specific audit is domain-specific in a general repo
- "Codex" reference remains in ARCHI_MAINTAINER_ACCEPTANCE_AUDIT.md title
- "Personal tooling stance" heading blurs force level in Manifesto
- Role-based tooling map in Manifesto is unpopulated

---

## Overall Assessment

**Coherent, low drift risk.**

The repository now meets the standard its own framework demands. The four-layer governance hierarchy is correctly implemented: each document respects its force level, content lives in the right place, cross-references use links, and the MUST/SHOULD distinction is properly enforced. The Constitution has been strengthened. The governance feedback loop has been demonstrated end-to-end.

Remaining issues are at the level of polish, scope decisions, and maturity (versioning, ownership). None represent structural, force-level, or consistency problems.

The gap between the framework's aspirations and the repository's execution — which was the central finding of the first review — has been closed.
