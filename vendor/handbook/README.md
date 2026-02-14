# handbook

This repository is the canonical, vendorable source for governance artifacts related to AI-assisted systems, audits, and maintainer acceptance.

## What this is
- Stable, conservative reference material
- Markdown and plain text only
- Intended to be vendored into other repositories via `git subtree`
- Includes templates for per-repo agent instruction files (AGENTS.md, CLAUDE.md, CONTRIBUTING.md)

## Governance hierarchy

This repository defines a four-layer governance system, ordered by force level:

1. **[Manifesto](MANIFESTO.md)** — values, optimisation targets, and selection pressures (why)
2. **[Tech Constitution](TECH_CONSTITUTION.md)** — minimum validity constraints (what must not break)
3. **[Reference Architecture](REFERENCE_ARCHITECTURE.md)** — ecosystem defaults and expected fit (what it should look like)
4. **[Playbook](PLAYBOOK.md)** — implementation, audits, and agent behaviour (how)

## Index

### Governance documents
- [Manifesto](MANIFESTO.md)
- [Tech Constitution](TECH_CONSTITUTION.md)
- [Reference Architecture](REFERENCE_ARCHITECTURE.md)
- [Playbook](PLAYBOOK.md)

### Audit prompts
- [AI Slop Audit](audits/AI_SLOP_AUDIT.md)
- [Agent Capability & Exposure Audit](audits/AGENT_CAPABILITY_AUDIT.md)
- [Archi Maintainer Acceptance Audit](audits/ARCHI_MAINTAINER_ACCEPTANCE_AUDIT.md)
- [Governance Consistency & Drift Audit](audits/GOVERNANCE_CONSISTENCY_AUDIT.md)
- [AGENTS.md Conformance & Drift Audit](audits/AGENTS_CONFORMANCE_AUDIT.md)

### Reports
- [Governance Consistency Audit — 2026-01-27](reports/REPORT-2026-01-27T222916Z.md)
- [Critical Review — 2026-02-12](reports/REPORT-2026-02-12-CRITICAL-REVIEW.md)
- [Critical Review v2 (Post-Remediation) — 2026-02-12](reports/REPORT-2026-02-12-CRITICAL-REVIEW-v2.md)

### Templates
- [Templates README](templates/README.md) — how to use templates for new repos
- [AGENTS.md template](templates/AGENTS.md.template)
- [CLAUDE.md template](templates/CLAUDE.md.template)
- [CONTRIBUTING.md template](templates/CONTRIBUTING.md.template)
- [Code reviewer agent](templates/.claude/agents/code-reviewer.md.template)

### Preferences
- [Owner Preferences](OWNER_PREFERENCES.md) — cross-repo conventions, patterns, and tool choices

### Infrastructure
- [Infrastructure Map](INFRASTRUCTURE_MAP.md) — end-to-end architecture map of all deployed components, data flows, and interactions

### Other
- [Superseded artifacts](superseded/)
- [Version](VERSION)

## Consumption (git subtree)

This repository is designed to be consumed via git subtree into other repositories and treated as read-only for downstream consumers:

```
git subtree add --prefix vendor/handbook https://github.com/matthewdart/handbook.git main --squash
```
