# Minimal Tech Constitution

## Scope and Role

This constitution defines the **minimum validity conditions** for technical systems, automation projects, and agent-assisted workflows.

It does **not** encode preferences, defaults, tooling choices, or optimisation strategies. Those live in the Manifesto and Playbook.

This document answers only one question:

> **Is this system still intelligible, governable, and recoverable over time?**

If a rule here is violated, the system is considered **invalid unless an explicit exception is recorded**.

---

## Invariant 1 — Inspectable Authority

There MUST exist an authoritative representation of system state that is:

* versioned
* inspectable without running the system
* understandable without proprietary tooling where feasible

If authoritative artefacts are non-textual, a **textual manifest describing provenance, generation, and semantics MUST exist**.

---

## Invariant 2 — Explicit Causality

All meaningful behaviour MUST be explainable as:

> *given trigger T, under rule R, action A occurred*

Triggers and rules MUST be explicit and discoverable.

Behaviour that depends on implicit framework conventions, hidden lifecycle hooks, or ambient runtime state is invalid.

---

## Invariant 3 — Bounded State Ownership

Authoritative state MUST NOT be primarily owned by:

* framework internals
* implicit runtime context
* UI-only configuration
* ephemeral execution environments (e.g. container filesystems, serverless functions)

Ephemeral state is permitted only if it is reconstructible from authoritative sources.

---

## Invariant 4 — Replayable Intent

For any significant operation, it MUST be possible in principle to:

* reconstruct the inputs
* identify the governing rules or contracts
* re-execute or simulate the operation

If replay is impractical, the **reason and limits MUST be explicit**.

---

## Invariant 5 — Explicit Boundaries

System boundaries MUST be explicit.

In particular:

* read vs write effects must be distinguishable
* contracts must define behaviour at boundaries
* side effects must be identifiable

Systems whose effects cannot be reasoned about at boundaries are invalid.

---

## Invariant 6 — Recorded Exceptions

Any deliberate violation of these invariants MUST:

* be explicit
* be documented with rationale and scope
* include an exit or review condition

Silent or undocumented exceptions are prohibited.

---

## Invariant 7 — Secrets Exclusion

Secrets and trust material MUST NOT be:

* committed to version-controlled repositories
* required to inspect or understand system behaviour
* treated as systems of record

Secrets are operational inputs, injected at runtime. They are never part of the authoritative representation of system state.

---

## Closing Clause

This constitution defines **what must not silently break**.

Preferences, defaults, and ecosystem choices belong elsewhere.

If these invariants hold, experimentation is permitted.
If they do not, optimisation is irrelevant.
