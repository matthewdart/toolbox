# Governance Consistency & Drift Audit Prompt

## Role

You are acting as an **independent governance auditor**.

Your task is to audit the following documents **as a system**, not in isolation:

* Working Manifesto — intent & selection pressures
* Minimal Tech Constitution — validity invariants
* Ecosystem Reference Architecture — ecosystem defaults & fit model
* Playbook — implementation, audits, and agent exploitation

Your goal is to detect **inconsistencies, overlap, misclassification, or drift** across these documents.

This is a **diagnostic audit**, not a rewrite exercise.

---

## 1. Establish Force Levels

First, reconstruct the **intended force hierarchy** implied by the documents:

* Manifesto → values, optimisation targets, selection pressures
* Constitution → hard validity constraints (“system is invalid if violated”)
* Reference Architecture → strong defaults & expected ecosystem fit
* Playbook → operationalisation, audits, and agent workflows

Confirm whether each document respects its intended force level.

Explicitly note any place where:

* a **default is written like a law**
* a **preference is treated as an invariant**
* an **operational rule leaks into the constitution**
* a **constitutional constraint is weakened into a suggestion**

---

## 2. Cross-Document Invariant Consistency

For each **constitutional invariant**, verify that:

* it is **not contradicted** by any other document
* it is **not silently weakened** elsewhere
* it is **not redundantly re-encoded** as a preference or default

Flag:

* contradictions
* ambiguous restatements
* places where agents could misinterpret authority

---

## 3. Defaults vs Laws Drift Check

Scan the Reference Architecture and Playbook for statements that:

* use MUST / SHOULD / REQUIRED language
* impose constraints on tooling, networking, state, or execution

Classify each such statement as one of:

* **Valid invariant** (belongs in the Constitution)
* **Strong default** (correctly placed)
* **Operational rule** (correctly in the Playbook)
* **Misclassified** (wrong document or wrong force level)

List any misclassifications with direct evidence.

---

## 4. Ecosystem Coherence Check

Assess whether the **ecosystem defaults**, taken together, form a coherent and non-contradictory system.

In particular, check consistency across:

* files & Git as coordination fabric
* headless execution & agent operability
* network exposure & trust model (private mesh vs public ingress)
* containerisation trajectory
* AI usage constraints (reasoning surface vs authority)
* secrets management (explicit gap handling)

Flag:

* missing assumptions
* conflicting defaults
* defaults that undermine each other when combined

---

## 5. Duplication & Shadow Doctrine Detection

Identify any concepts that are:

* repeated across documents
* named differently but semantically identical
* partially restated with different force levels

For each case, state whether the duplication represents:

* **intentional reinforcement**
* **accidental shadow doctrine**
* **early drift risk**

---

## 6. Agent Misinterpretation Risk

Evaluate the documents **from an agent’s point of view**.

Identify any places where an agent could reasonably:

* treat a default as mandatory
* treat a preference as law
* miss an important constraint because it is implicit
* follow the Playbook in a way that violates the Constitution

List concrete misinterpretation risks.

---

## 7. Drift Signals (Early Warning)

Look for signs of **incipient drift**, such as:

* increasing specificity in defaults
* platform or tool identity creeping into invariants
* lifecycle ownership reappearing implicitly
* containerisation sliding from packaging to platform
* secrets or networking rules becoming implied rather than explicit

Do **not** propose fixes at this stage — only surface signals.

---

## 8. Output Format (Strict)

Produce the audit in the following structure:

1. **Executive Summary** (≤10 lines)
2. **Confirmed Alignments**
3. **Force-Level Violations** (with quotes and references)
4. **Drift & Ambiguity Risks**
5. **Agent Interpretation Risks**
6. **Gaps & Explicitly Acknowledged Unknowns**
7. **Overall Assessment** — one of:

   * Coherent, low drift risk
   * Coherent, moderate drift risk
   * Incoherent, requires intervention

Evidence first. Interpretation second. Recommendations only if explicitly requested.
