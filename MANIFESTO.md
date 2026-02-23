# Working Manifesto — Friction, Insight, and Leverage

## Purpose

This manifesto exists to preserve the conditions under which work feels **frictionless, insightful, and sustainable**.

It is not a product vision or a tooling roadmap. It is a set of **selection pressures** for how tools, systems, and AI should be adopted and combined over time.

The primary optimisation target is:

> **Insight per unit of effort, sustained over time.**

---

## Core outcomes to protect

* High signal-to-noise learning loops
* Inspectable reality over inferred abstractions
* Momentum without cognitive drag
* Optionality preserved as long as possible

If these degrade, the system is regressing.

---

## Observed patterns that worked

1. **Data-first, UI-later**
   Understanding preceded presentation.

2. **Minimal plumbing**
   Progress without heavy ETL, orchestration, or brittle glue.

3. **Queries as hypotheses**
   Errors and mismatches were learning signals, not failures.

4. **Tight inner loop**
   Small changes produced immediate feedback.

5. **Domain-native constraints**
   Reality was accepted early rather than abstracted away.

---

## Design principles (portable)

* Prefer **inspectability over elegance**
* Defer structure until **pressure appears**
* Treat mismatches as **assets**
* Keep systems **conversational**, not opaque
* Optimise for **sustained curiosity**, not short-term output

---

## Explicit anti-goals

* Platforms for their own sake
* Premature generalisation
* Tooling that demands total understanding upfront
* Automation before epistemic stability
* Infrastructure work disguised as insight work

**Non-goal clarification:** these constraints apply to what is *kept and integrated*, not to what is *tried and explored*.

Messy experiments are allowed. Inertia is not.

---

## Personal tooling stance

### Ecosystem, not stack

* No single centre of gravity
* Tools are replaceable and must earn their place
* Edges may sprawl; convergence points must not

### AI as reasoning surface

AI is used to:

* Inspect
* Question
* Reframe
* Stress-test interpretations

Not to hide complexity or prematurely lock in structure.

### Minimal code, maximal semantics

* Prefer declarative artefacts over glue code
* Push interpretation upward, keep adapters disposable
* Tolerate some mess to preserve reversibility

---

## Convergence rules (anti-sprawl)

* Tools must converge through **existing primitives** (files, schemas, text)
* New centres of gravity are treated as high-risk
* The system must remain understandable without any single tool present

---

## Tool admission checklist

A tool may move beyond *experimental* only if:

1. It removes concrete local friction immediately
2. Inputs and outputs are easily inspectable
3. It interoperates via existing primitives
4. It has a clear exit path
5. It occupies a defined role (not a vague promise)

If answers are unclear, the tool remains provisional.

---

## Tool lifecycle states

* **Experimental** — low commitment, high learning
* **Active** — currently earns its keep
* **Dormant** — retained but off the critical path
* **Archived** — outputs kept, tool forgotten

Everything has a state. Inertia is not a state.

---

## Role-based tooling map (stable abstraction)

* Reasoning & dialogue surface
* Data inspection & querying
* Long-lived thinking substrate
* Capture & ingestion
* Automation & glue (experimental by default)
* Visualisation & presentation (on-demand)

At most one *active* tool per role.

---

## Forward test

Before expanding the system, ask:

> **Will this increase insight per unit of effort — or just surface area?**

If the answer is not clearly the former, pause.

---

## Refactoring discipline (anti-drift)

Refactoring is allowed only if it **reduces complexity** or **makes invariants more explicit**.

Refactors that merely reshuffle code, introduce abstractions, or align with generic "best practices" without clear payoff are considered regression.

For the full refactoring process, acceptance criteria, and coherence checks, see [PLAYBOOK.md](PLAYBOOK.md).

---

## Living status

This manifesto is expected to evolve.

Revise it when:

* Friction accumulates
* Curiosity drops
* Tooling inertia appears
* Maintenance outweighs insight

When that happens, update the manifesto — not just the tools.
