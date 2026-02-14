# Ecosystem Reference Architecture — Defaults & Fit Model

## Scope and Role

This document defines the **baseline ecosystem shape** that implementations are expected to fit into by default.

It encodes **strong defaults** that have proven coherent, composable, and durable across projects. These defaults are **presumptive, not mandatory**.

Deviations are allowed, but they should be:

* intentional
* explicit
* understood in terms of trade-offs

This document does **not** define validity (see the [Tech Constitution](TECH_CONSTITUTION.md)), nor procedures (see the [Playbook](PLAYBOOK.md)), nor values (see the [Manifesto](MANIFESTO.md)).

It answers one question:

> **Does this system fit the ecosystem it is meant to live in?**

---

## Relationship to Other Governance Artifacts

* **[Manifesto](MANIFESTO.md)** — defines optimisation targets and selection pressures (why)
* **[Tech Constitution](TECH_CONSTITUTION.md)** — defines minimum validity constraints (what must not break)
* **Reference Architecture (this document)** — defines ecosystem defaults and expected fit (what it should look like)
* **[Playbook](PLAYBOOK.md)** — defines execution, audits, and agent behaviour (how)

---

## 1. Canonical Primitives

### 1.1 Files as the Primary Coordination Medium

**Default**

* Files (textual where possible) are the primary medium for coordination, persistence, and inspection.

**Rationale**

* Diffable, inspectable, durable
* Tool-agnostic
* Friendly to both humans and agents

**Expected Fit**

* Canonical state round-trips through files
* Non-text artefacts have textual manifests

**Deviation Guidance**

* Allowed when file-based representation is impractical
* Requires explicit identification of the alternative authority and its inspection path

---

### 1.2 Git as the Control Plane

**Default**

* Git-hosted repositories are the coordination and governance layer.

**Rationale**

* Versioned history
* Explicit change control
* Natural audit trail

**Expected Fit**

* Specs, contracts, prompts, and artefacts live in repositories
* Diffs explain change

**Deviation Guidance**

* Allowed for ephemeral or exploratory work
* Long-lived systems must declare an equivalent control plane

---

## 2. Integration & Interface Patterns

### 2.1 Protocol-First Interfaces

**Default**

* Interfaces are defined via explicit protocols (HTTP + JSON/YAML by default).

**Rationale**

* Language-agnostic
* Inspectable
* Contract-friendly

**Expected Fit**

* Behaviour is defined by schemas or OpenAPI-like contracts
* Clients and agents rely on contracts, not code conventions

**Deviation Guidance**

* Alternative protocols permitted with documented schemas and tooling rationale

---

### 2.2 Tool Boundaries as Explicit Services

**Default**

* Tools expose capabilities through explicit service boundaries rather than embedded calls.

**Rationale**

* Clear ownership
* Replaceability
* Agent operability

**Expected Fit**

* Capabilities are discoverable
* Inputs, outputs, and errors are explicit

**Deviation Guidance**

* Embedded tooling allowed for host-platform constraints
* Boundary must remain conceptually explicit

---

## 3. State & Projection Model

### 3.1 Canonical vs Derived

**Default**

* One canonical representation exists for any given domain concept.
* Views, diagrams, reports, and exports are derived.

**Rationale**

* Prevents divergence
* Enables regeneration

**Expected Fit**

* Derived artefacts can be regenerated or are explicitly declared hand-authored

**Deviation Guidance**

* Multiple authorities require explicit reconciliation logic and justification

---

### 3.2 Regeneration Over Manual Duplication

**Default**

* Mechanical derivation is preferred to manual duplication.

**Rationale**

* Reduces drift
* Preserves trust in artefacts

**Expected Fit**

* Pipelines exist or are planned for regeneration

**Deviation Guidance**

* Manual artefacts permitted when regeneration cost outweighs benefit

---

## 4. Execution & Interaction Model

### 4.1 Headless-First Paths

**Default**

* All important capabilities have a headless execution path.

**Rationale**

* Automation
* Testability
* Agent access

**Expected Fit**

* UIs are optional
* Core logic is callable without UI context

**Deviation Guidance**

* UI-only systems require explicit justification and compensating controls

---

### 4.2 UI as Signal Surface

**Default**

* UIs are used to observe, explore, and trigger — not to own logic or state.

**Rationale**

* Preserves inspectability
* Avoids hidden coupling

**Expected Fit**

* UI context is observable and transient

**Deviation Guidance**

* UI-owned state must be exportable and documented

---

## 5. Agent Operating Assumptions

### 5.1 Agents as Workers

**Default**

* Agents act as bounded workers, not authorities.

**Rationale**

* Preserves human oversight
* Prevents silent drift

**Expected Fit**

* Agents propose changes via artefacts
* Evidence accompanies action

**Deviation Guidance**

* Autonomous mutation requires explicit scope and logging

---

### 5.2 Evidence and Provenance

**Default**

* Agent actions produce inspectable evidence.

**Rationale**

* Auditability
* Trust

**Expected Fit**

* Outputs are stored
* Decisions reference canonical sources

---

## 6. Runtime Substrate

**Default**

* Unix-like operating systems (macOS, Linux)
* POSIX-compatible shell environment
* Local filesystem semantics

**Rationale**

* Enables headless execution
* Supports SSH-based control
* Predictable process and file semantics for agents

**Expected Fit**

* Core workflows must be operable in a non-UI, shell-based environment
* Tooling assumes filesystem access and standard process invocation

**Deviation Guidance**

* Non-POSIX environments require an explicit compatibility or abstraction layer

---

## 7. Network Exposure & Trust Model

**Default**

* Services SHOULD NOT be exposed directly to the public internet by default.
* Device-to-device and internal service communication uses a private mesh network.

**Preferred Realisation**

* Tailscale for private connectivity between owned or managed devices

**Public Exposure Rule**

* Services that need to be internet-facing SHOULD be exposed via a managed edge tunnel.

**Preferred Realisation**

* Cloudflare Tunnels for ingress, TLS termination, and coarse access control

**Constraints**

* Edge services are not systems of record
* Authentication and authorization should still be enforceable at the origin

**Deviation Guidance**

* Direct public exposure requires explicit justification and threat consideration

---

## 8. Secrets & Trust Material (Explicit Gap)

**Current State**

* Secrets management is intentionally under-specified.

**Constitutional Constraints**

The following constraints are validity invariants defined in the [Tech Constitution](TECH_CONSTITUTION.md) (Invariant 7), not defaults:

* Secrets MUST NOT be committed to repositories
* Secrets MUST NOT be required to understand system behaviour
* Secrets are never systems of record

**Operational Expectation**

* Secrets are injected at runtime (environment variables, secure stores, or equivalent).

**Known Gap**

* A unified, explicit secrets management strategy is not yet defined.
* This gap is acknowledged and tracked, not ignored.

---

## 9. Tooling Defaults (Non-Exhaustive)

This section makes **explicit the current concrete tools** that realise the ecosystem defaults described above. These are **defaults, not commitments**. Each exists because it currently fits the reference architecture better than known alternatives.

### 9.1 Connectivity & Trust Envelope

**Default Tools**

* Tailscale — mesh connectivity between devices and servers
* Cloudflare — ingress, TLS termination, and coarse security boundaries

**Why They Fit**

* Reduce network configuration surface area
* Preserve explicit trust boundaries
* Fail visibly and locally

**Constraints**

* Neither tool is a system of record
* Authentication and authorization should still be enforceable at the origin

**Exit Path**

* Replaceable by any solution providing equivalent explicit connectivity and edge control

---

### 9.2 Human Trigger & Capture Layer

**Default Tools**

* Apple Shortcuts — human-triggered automation and capture

**Why It Fits**

* Low-friction capture from mobile contexts
* Acts purely as an event bridge

**Constraints**

* No business logic
* No authoritative state
* Must trigger headless-capable systems

**Exit Path**

* Any automation or trigger system with equivalent event-bridging capability

---

### 9.3 Long-Lived Thinking & Knowledge Substrate

**Default Tools**

* Obsidian — local-first knowledge graph over Markdown

**Why It Fits**

* File-based
* Git-compatible
* Tool-independent knowledge representation

**Constraints**

* Notes must remain intelligible without Obsidian
* Plugins may not become authoritative

**Exit Path**

* Any Markdown-native knowledge system with local storage and export

---

### 9.4 Capture Devices & Ingestion Sources

**Default Tools**

* reMarkable — handwritten capture and annotation

**Why It Fits**

* Low-friction capture
* Clear separation between capture and interpretation

**Constraints**

* Device output is not authoritative
* Raw exports must be preserved

**Exit Path**

* Any capture device that allows raw data export and downstream processing

---

### 9.5 Code, Specs, and Coordination

**Default Tools**

* GitHub — hosted Git repositories and issue/PR workflows

**Why It Fits**

* Versioned coordination
* Reviewable change
* Agent-compatible workflows

**Constraints**

* Git semantics are the dependency, not the hosting vendor

**Exit Path**

* Any Git-compatible hosting platform

---

### 9.6 AI Reasoning & Execution Layer

**Default Tools**

* OpenAI (ChatGPT, Codex-class models) — reasoning, analysis, and bounded execution

**Why It Fits**

* Strong performance on text, code, and structured reasoning
* Supports both conversational exploration and headless execution modes
* Compatible with contract-first, artifact-producing workflows

**Constraints**

* AI systems are not systems of record
* No authoritative state may live exclusively in model memory or chat history
* Outputs must be externalised as files, diffs, or artefacts

**Exit Path**

* Any AI system capable of:

  * operating over explicit inputs
  * producing inspectable outputs
  * respecting external contracts and boundaries

---

Each default must have a clear exit path.

---

## 10. Conformance Declaration

Each project SHOULD include a short statement declaring one of:

* **Conforms** — fits the reference architecture
* **Partially Conforms** — deviations documented
* **Divergent** — alternative ecosystem declared

This declaration is informational, not a gate.

---

## 11. Portability & Containerisation Trajectory

This ecosystem is expected to become increasingly **container-packaged and portable by default** over time. This is a direction of travel, not a hard requirement. The goal is to reduce environment-specific friction while preserving inspectability, replaceability, and headless operability.

### 11.1 Containers as Packaging, Not Platform

**Default**

* Containers are treated as **packaging and execution envelopes**, not as systems of record or identity.

**Rationale**

* Improves portability and reproducibility
* Reduces host-specific coupling
* Preserves replaceability of runtime environments

**Constitutional Constraints**

The following are validity invariants from the [Tech Constitution](TECH_CONSTITUTION.md) (Invariant 3), not defaults:

* Authoritative state MUST NOT reside in ephemeral execution environments such as container filesystems.
* Behaviour MUST remain explainable without container tooling (Invariant 2).

**Ecosystem Defaults**

* Configuration and secrets SHOULD be injected at runtime.
* Capabilities SHOULD remain callable headlessly without UI context.

---

### 11.2 Container-Ready, Then Container-Packaged

**Expected Fit**

* Each significant tool or service should have:

  * a documented headless entry point
  * declared runtime requirements
  * a clear boundary between canonical state and derived outputs

**Trajectory**

* First make systems **container-ready** (portable without containers)
* Then make them **container-packaged** (container images available)

---

### 11.3 Headless-First, Container-Optional

**Default**

* Every significant tool or service SHOULD be runnable headlessly **without containers**.
* Containerisation is an additive portability layer, not a prerequisite.

**Rationale**

* Preserves debuggability
* Avoids hidden lifecycle ownership

**Expected Fit**

* Single explicit entrypoint per tool/service
* Identical behaviour inside and outside containers

---

### 11.4 State & Configuration

**Default**

* Containers are treated as ephemeral.

**Constraints**

* Writable state SHOULD be mounted via volumes or external stores only.
* Configuration and secrets SHOULD be injected at runtime.

**Deviation Guidance**

* Any container-internal persistence requires explicit justification.

---

### 11.5 Networking & Exposure

**Default**

* Containerised services follow the same trust model as non-containerised services.

**Expected Fit**

* Private communication over mesh networking
* No direct public exposure by default
* Public ingress only via managed edge tunnels

**Preferred Realisation**

* Tailscale for mesh connectivity
* Cloudflare Tunnels for public exposure

**Rationale**

* Maintains a single, consistent threat model

---

## 12. Ecosystem Repository Map

The ecosystem is composed of repositories that fall into three categories: **governance**, **infrastructure**, and **project**. Agents working in any repo should understand the overall map — particularly which repos provide shared services that other repos depend on.

### 12.1 Governance

| Repository | Purpose |
|---|---|
| **handbook** | Governance upstream — Manifesto, Constitution, Reference Architecture, Playbook, Owner Preferences, templates, audits. Vendored into all project repos via `git subtree` at `vendor/handbook/`. |

### 12.2 Infrastructure

| Repository | Purpose | Consumed by |
|---|---|---|
| **toolbox** | Reusable skills (executable scripts) and GitHub Actions workflows (`build-arm-image.yml`, `deploy-stack.yml`). Skills are callable from CLI, CI, or agents. | All repos that build ARM images or deploy to the VM reference toolbox workflows. Skills are installed on development machines and the VM. |

### 12.3 Project Repositories

| Repository | Purpose | Tier |
|---|---|---|
| **remarkable-pipeline** | reMarkable tablet data pipeline — ingestion, rendering, OCR, MCP server | Tier 2 |
| **health-ledger-mcp** | Apple Health analytics — SQL data layer and MCP server | Tier 1 |
| **health-ledger** | Apple Health export ingestion and SQL gateway (upstream of health-ledger-mcp) | Tier 2 |
| **archi-mcp-bridge** | ArchiMate modelling tool MCP bridge via jArchi | Tier 1 |
| **pptx-mcp-bridge** | PowerPoint MCP bridge via Office.js add-in | Tier 2 |
| **obsidian-copilot** | Obsidian plugin — AI copilot for knowledge management | Tier 1 |
| **obsidian-atlas** | Obsidian plugin — visual knowledge graph | Tier 1 |
| **obsidian-california** | Obsidian plugin — early stage | Tier 1 |
| **archi-scripts** | Utility scripts for Archi modelling tool | Tier 1 |
| **pipeline-template** | Template repo for new pipeline-style projects | Tier 2 |

### 12.4 Deployment Model

Each service repo is self-contained for production deployment:

- Each repo defines its own Dockerfile and container configuration
- Containers run independently on the Oracle Cloud ARM VM
- Cloudflared runs on the VM host (not as a container), routing to services via `localhost:<port>`
- Inter-service communication, when needed, uses Tailscale — no shared Docker network required

### 12.5 Relationships

```
handbook (governance)
  └── vendored into all repos at vendor/handbook/

toolbox (infrastructure)
  ├── .github/workflows/  → referenced by project repo CI/CD
  └── skills/             → installed on dev machines and VM

project repos
  ├── consume handbook (vendored)
  ├── consume toolbox workflows (CI reference)
  └── deploy independently to the VM as standalone containers
```

---

## 13. Living Status

This reference architecture is expected to evolve more slowly than playbooks, but faster than the constitution.

Revise it when:

* defaults stop paying their way
* friction accumulates across multiple projects
* new primitives consistently outperform old ones

When that happens, update this document — not just individual implementations.
