# Workspace Hygiene Audit — Prompt

## Purpose

This prompt is intended to be given to a coding agent with access to one or more development machines. Its task is to audit the state of all Git repositories across the workspace: identifying uncommitted work, sync drift, stale branches, orphaned clones, and configuration inconsistencies.

The goal is diagnosis and remediation. The output should surface concrete issues, prioritise them by risk of data loss or drift, and — where safe — perform the cleanup directly.

---

## Prompt

You have access to one or more development machines. Your task is to audit every Git repository across the workspace for hygiene issues: uncommitted changes, remote sync drift, stale branches, orphaned or duplicate clones, and configuration problems.

This is a DIAGNOSTIC AND REMEDIATION task. For each issue found, you will classify it and either fix it directly (if safe) or flag it for human decision. Base all conclusions on evidence. Do not guess remote state — fetch first.

## Scope & assumptions

- The workspace spans all machines you have access to (local and remote via SSH).
- Repositories may exist in multiple locations (e.g. a project cloned on both a laptop and a cloud instance).
- Some repositories may be forks, subtrees, or vendored copies — identify these rather than treating them as duplicates.
- You have permission to fetch, pull, push (to non-protected branches), and delete local branches. You do NOT have permission to force-push to main/master or delete remote branches without explicit confirmation.

## Pre-flight

Before inspecting individual repositories:

1. **Enumerate all repositories** across all accessible machines. Record each repo's path, current branch, and remote URL(s).
2. **Fetch all remotes** for every repository. Do not inspect sync state against stale remote refs.
3. **Identify duplicates and relationships** — same remote URL on multiple machines, forks (different remote URL but shared history), subtrees, vendored copies.

Present the full inventory before proceeding to inspection.

## What to inspect (mandatory)

### 1) Uncommitted work

For each repository, check for:
- Staged but uncommitted changes
- Unstaged modifications to tracked files
- Untracked files that appear intentional (not build artifacts or editor temp files)
- Stashed changes

Classify each finding:
- **Commit-ready** — coherent changeset that should be committed as-is
- **Needs review** — changes that require human decision on whether to commit, discard, or split
- **Discard-safe** — build artifacts, editor state, OS metadata that can be cleaned

### 2) Remote sync state

For each repository, check:
- Is the current branch ahead of its upstream? (unpushed commits)
- Is the current branch behind its upstream? (needs pull)
- Are there local branches with no upstream tracking branch?
- Are there remote branches that have been merged or deleted upstream but still tracked locally?

Classify each finding:
- **Push-ready** — local commits that are clean and should be pushed
- **Pull-ready** — behind upstream with no local changes (safe to fast-forward)
- **Diverged** — both ahead and behind (needs rebase or merge decision)
- **Orphaned local branch** — no upstream, no recent commits
- **Stale remote tracking** — remote branch deleted or merged

### 3) Branch hygiene

For each repository, check:
- Local branches that have been fully merged into the default branch
- Local branches with no commits in the last 60 days
- Remote branches (on GitHub/origin) that are fully merged but not deleted

Present branch hygiene as a table: branch name, last commit date, merge status, recommendation.

### 4) Repository configuration

For each repository, check:
- Is user.email set and consistent across machines? (watch for privacy-violating email addresses on public repos)
- Is user.name set?
- Are remote URLs using the expected protocol (SSH vs HTTPS)?
- Are there any shallow clones that should be unshallowed?
- Is the default branch name consistent with the remote?

### 5) Cross-machine consistency

For repositories that exist on multiple machines:
- Are they on the same branch?
- Are they at the same commit?
- Does one have uncommitted work that the other doesn't?
- Are remote URLs identical?

Flag any divergence. Recommend which copy is canonical and which should be refreshed or removed.

### 6) Orphaned and archived repositories

Check for:
- Local clones of repositories that have been archived or deleted on the remote
- Local clones that have no remote configured
- Directories that look like they were once Git repositories (contain .git artifacts) but are broken

Recommend: delete, archive locally, or investigate.

### 7) Stash and worktree inventory

For each repository:
- List all stashes with their descriptions and dates
- List all worktrees
- Flag stashes older than 30 days as candidates for review or drop

## Remediation protocol

For each finding, apply one of:

| Action | When | Requires confirmation |
|--------|------|-----------------------|
| git pull --ff-only | Behind upstream, no local changes | No |
| git push | Ahead of upstream, clean commits | No |
| Commit and push | Commit-ready changes identified | Yes — present diff summary first |
| Delete local branch | Fully merged into default branch | No |
| Delete local branch | Orphaned, no recent commits | Yes |
| Delete remote branch | Fully merged, confirmed stale | Yes |
| Force-push | Rebased branch | Yes — explain what changed |
| Delete local clone | Archived/deleted remote, or confirmed duplicate | Yes |
| Fix git config | Email privacy issue, protocol mismatch | No |
| Discard changes | Build artifacts, editor state | No |

Never force-push to main/master. Never delete a branch that has unmerged commits without explicit confirmation.

## Analysis to perform

After completing all inspections, answer:

- Which repositories have the highest risk of lost work? (uncommitted changes + no remote backup)
- Which repositories are cleanest? (fully synced, no stale branches, consistent config)
- Are there any repositories that should be consolidated or removed?
- What is the overall hygiene score of the workspace?

## Scoring rubric

For each repository, score 0-2 on:
1) Commit hygiene (no uncommitted work, clean history)
2) Sync state (up to date with remote, no divergence)
3) Branch hygiene (no stale branches, merged branches cleaned)
4) Configuration (correct email, consistent protocol, no shallow clones)
5) Cross-machine consistency (if applicable)

Highlight any repository averaging ≤1.

## Output format

Produce a structured report with:

1. **Workspace inventory** — all repos, all machines, with remote URLs and relationships
2. **Executive summary** — overall hygiene level (clean / needs attention / at risk)
3. **Actions taken** — what was remediated automatically
4. **Actions requiring confirmation** — presented with evidence and recommendation
5. **Findings by category** — with per-repo evidence
6. **Risk hotspots** — repositories ranked by data-loss or drift risk
7. **Hygiene scorecard** — per-repo scores in table format

Be precise and evidence-based. Do not guess — fetch and verify.

---

## Intended use

- Run periodically (weekly or fortnightly) as a workspace health check
- Run before and after extended periods of work across multiple machines
- Run when onboarding a new development machine to align it with existing workspace state
- Use as a pre-cleanup diagnostic before archiving or decommissioning a machine

This prompt can be followed up with: "Proceed with all recommended remediations" to execute the flagged actions.
