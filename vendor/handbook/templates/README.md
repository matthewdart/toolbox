# Templates

This directory contains canonical templates for per-repo agent instruction and documentation files.

## Purpose

Every repository in the ecosystem should have standardised agent docs. These templates provide the starting point. Copy them on repo creation, then adapt the `REPO-SPECIFIC` sections.

## Relationship to governance docs

The templates operationalise the handbook's four-layer governance hierarchy:

- **[Manifesto](../MANIFESTO.md)** informs AGENTS.md values and principles
- **[Tech Constitution](../TECH_CONSTITUTION.md)** enforces AGENTS.md non-negotiable rules
- **[Reference Architecture](../REFERENCE_ARCHITECTURE.md)** shapes AGENTS.md architecture and defaults
- **[Playbook](../PLAYBOOK.md)** defines AGENTS.md workflow and audit patterns

## Files

| Template | Purpose | Audience | Required? |
|---|---|---|---|
| `AGENTS.md.template` | Agent behaviour rules and repo-specific constraints | All AI agents (Claude, Codex, Copilot, etc.) | Yes, all repos |
| `CLAUDE.md.template` | Claude Code-specific notes (thin wrapper around AGENTS.md) | Claude Code only | Yes, all repos |
| `CONTRIBUTING.md.template` | Human contributor guide (bug reports, PRs, dev setup) | Human contributors | Optional |
| `.claude/agents/code-reviewer.md.template` | Code review sub-agent persona | Claude Code sub-agents | Optional |

## Workflow tiers

The AGENTS.md template supports two workflow tiers. Each repo declares which tier it uses.

- **Tier 1 (lightweight, default):** Read context, state assumptions, propose, apply. For experimental, small, or single-purpose repos.
- **Tier 2 (structured):** Full Research / Convergence / Execution phases with mandatory Steps A-F. For repos with requirements, acceptance criteria, or stability contracts.

Repos may also use an optional **mode system** overlay (Prototype/Stabilised) where both tiers coexist, switchable per-task.

Repos start at Tier 1. Structure appears when pressure demands it.

## How to use

1. Copy the relevant `.template` files to your repo root (dropping the `.template` suffix)
2. Replace all `<!-- REPO-SPECIFIC -->` sections with repo-specific content
3. Remove or keep `<!-- IF APPLICABLE -->` sections as appropriate
4. Vendor the handbook: `git subtree add --prefix vendor/handbook <url> main --squash`
5. Update the Governance section paths to point to the vendored handbook
