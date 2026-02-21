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

### Templates (copy and customise per repo)

| Template | Purpose | Audience | Required? |
|---|---|---|---|
| `AGENTS.md.template` | Agent behaviour rules and repo-specific constraints | All AI agents (Claude, Codex, Copilot, etc.) | Yes, all repos |
| `CLAUDE.md.template` | Claude Code entry point — imports AGENTS.md + preferences via `@` syntax | Claude Code only | Yes, all repos |
| `CONTRIBUTING.md.template` | Human contributor guide (bug reports, PRs, dev setup) | Human contributors | Optional |

### Ecosystem agents (distributed via symlink)

These live in [`../agents/`](../agents/) and are distributed to consuming repos via a whole-directory symlink (see [Agent distribution](#agent-distribution) below). They require no per-repo customisation.

| Agent | Purpose | Colour |
|---|---|---|
| `code-reviewer-python.md` | Python code review with ecosystem conventions (future annotations, pathlib, dataclasses, Protocol) | cyan |
| `code-reviewer-typescript.md` | TypeScript code review with ecosystem conventions (strict mode, interfaces, vitest, npm) | cyan |
| `code-reviewer-java.md` | Java code review for Eclipse/OSGi plugin context (archi-mcp-bridge, jArchi constraints) | cyan |
| `code-reviewer-sql.md` | SQL code review with ecosystem conventions (DuckDB, views as modelling surface, numbered files) | cyan |
| `handbook-enforcer.md` | Audit a repo against the full handbook governance hierarchy | yellow |
| `handbook-maintainer.md` | Review sessions and identify new patterns for handbook evolution | green |
| `contract-validator.md` | Verify code implements what contracts promise (CONTRACT.md, contract.v1.json, OpenAPI) | red |
| `fleet-auditor.md` | Audit MCP fleet config, runtime state, and portal registrations for consistency | blue |
| `documentation-sync.md` | Detect documentation drift — adapts scope by workflow tier (Tier 1 / Tier 2) | magenta |
| `impact-tracer.md` | Trace downstream effects of a change across code, contracts, docs, infra, and cross-repo | orange |
| `worktree-coordinator.md` | Track multi-worktree session state, phase status, and merge readiness | white |

## Workflow tiers

The AGENTS.md template supports two workflow tiers. Each repo declares which tier it uses.

- **Tier 1 (lightweight, default):** Read context, state assumptions, propose, apply. For experimental, small, or single-purpose repos.
- **Tier 2 (structured):** Full Research / Convergence / Execution phases with mandatory Steps A-F. For repos with requirements, acceptance criteria, or stability contracts.

Repos may also use an optional **mode system** overlay (Prototype/Stabilised) where both tiers coexist, switchable per-task.

Repos start at Tier 1. Structure appears when pressure demands it.

## How to use (initial setup)

1. Copy the relevant `.template` files to your repo root (dropping the `.template` suffix)
2. Replace all `<!-- REPO-SPECIFIC -->` sections with repo-specific content
3. Remove or keep `<!-- IF APPLICABLE -->` sections as appropriate
4. Vendor the handbook: `git subtree add --prefix vendor/handbook https://github.com/matthewdart/handbook.git master --squash`
5. Update the Governance section paths to point to the vendored handbook
6. Set up the agent symlink (see below)

## Agent distribution

Ecosystem agents are shared via the handbook and require no per-repo customisation. They are distributed using a whole-directory symlink from `.claude/agents/` to the vendored handbook.

### Setting up the symlink

After vendoring the handbook, create the symlink:

```bash
# Remove any existing .claude/agents/ directory (back up local agents first)
rm -rf .claude/agents

# Create the symlink
ln -s ../vendor/handbook/agents .claude/agents

# Commit the symlink
git add .claude/agents
git commit -m "link ecosystem agents from vendored handbook"
```

The symlink is relative (`../vendor/handbook/agents`), so it works on any machine that has the repo cloned. It is committed to git and travels with the repo.

### How it works

```
consuming-repo/
  .claude/
    agents -> ../vendor/handbook/agents   (symlink, committed to git)
  vendor/
    handbook/                              (git subtree, committed)
      agents/
        handbook-enforcer.md
        code-reviewer-python.md
        ...
```

Claude Code discovers agents at `.claude/agents/*.md`. The symlink makes it see the vendored handbook agents transparently.

### Update flow

When the handbook adds or updates agents:

```bash
git subtree pull --prefix vendor/handbook https://github.com/matthewdart/handbook.git master --squash
```

The symlink doesn't change — it still points to `../vendor/handbook/agents`. But the content behind it updates automatically. No additional steps required.

### Portability

- **macOS / Linux**: symlinks work natively
- **GitHub Actions (Ubuntu)**: symlinks work natively
- **Windows**: requires `core.symlinks=true` in git config (not relevant for this ecosystem)

## Keeping the handbook up to date

The vendored handbook is a snapshot. It will not update automatically.

### When to update

- After handbook version bumps (check `VERSION` in the handbook repo)
- Before running conformance audits
- When starting a new phase of work on a repo

### How to update

```
git subtree pull --prefix vendor/handbook https://github.com/matthewdart/handbook.git master --squash
```

### Checking for staleness

Compare your vendored version against upstream:

```
cat vendor/handbook/VERSION
# Then check upstream:
gh api repos/matthewdart/handbook/contents/VERSION --jq '.content' | base64 -d
```

If the versions differ, pull the update.

## Auditing conformance

Use the [AGENTS.md Conformance Audit](../audits/AGENTS_CONFORMANCE_AUDIT.md) prompt to check a repo's agent docs against the handbook templates. Run it:

- After initial setup to verify correctness
- Periodically to detect drift
- After handbook version bumps to check alignment
