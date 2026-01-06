# toolbox

A personal toolbox of small, deterministic scripts (“skills”) used by humans and agents (e.g. Codex) to perform repeatable, side-effecting workflows.

This repository is intentionally boring, explicit, and reliable.

---

## Purpose

toolbox exists to solve a specific problem:

Repeated workflows involving GitHub, files, and automation should not be re-implemented in prompts.

Instead:
- they are encoded once as skills
- versioned
- callable from scripts, Codex, CI, or SSH
- and reused across projects

---

## What is a “skill”?

In this repository, a skill is:

- a single executable script
- with a stable command-line interface
- performing one well-defined side effect
- deterministic given the same input
- safe to call from Codex without reinterpretation

A skill is not:
- a chat interface
- an exploratory agent
- a place for policy debate
- stateful or interactive

Think: syscall, not assistant.

---

## Repository structure

toolbox/
- skills/        Executable skills (Codex is allowed to call these)
- lib/           Shared helpers (logging, assertions, gh helpers, etc.)
- templates/     Shared markdown / document templates
- AGENTS.md      Contract for agent behavior when using this repo
- README.md

---

## Available skills

- canvas_markdown: extract markdown from a ChatGPT canvas share URL. Usage: `canvas_markdown <url>` or `echo <url> | canvas_markdown` (use `-o <path>` to write a file).
- create_private_gist: create a private GitHub gist from files or stdin. Usage: `create_private_gist <file> [<file> ...]` or `cat input.txt | create_private_gist -f input.txt` (use `-d <desc>` for a description).

---

## Design principles

All skills in this repository MUST follow these rules:

1. No sudo  
   Skills run as an unprivileged user. All system setup is out of scope.

2. User-space only  
   No systemd, no package installs, no global filesystem mutation.

3. Deterministic behavior  
   Same input produces the same output shape. No hidden prompts or interaction.

4. Fail fast  
   Missing prerequisites (for example gh not authenticated) must error clearly.

5. Explicit contracts  
   Inputs via stdin or flags. Outputs must be machine-consumable.

---

## Codex usage model

Codex is expected to:

- call skills directly
- not re-implement their logic
- not inline gh, git, or other workflows already encoded here

Example instruction to Codex (conceptual):

When capturing distilled content, use the create_handoff_gist skill.  
Do not call gh gist create directly.

This contract is enforced via AGENTS.md.

---

## GitHub authentication

Skills that interact with GitHub assume:

- gh is installed
- gh is already authenticated
- authentication is provided by the environment (PAT, keychain, or CI token)

Skills must not:
- prompt for credentials
- embed tokens
- attempt gh auth login

---

## Networking and Tailscale

- Tailscale is used only on machines we control (laptops, servers, VMs)
- Skills may assume outbound network access where appropriate
- Skills must not assume:
  - private networking inside Codex Environments
  - SSH access to Codex Environments

Codex Environments are treated like locked-down CI runners.

---

## Installation and usage

Typical usage pattern on a machine where Codex runs:

Clone toolbox into a stable location, for example ~/toolbox, and add ~/toolbox/skills to PATH.

Once installed, skills are invoked like normal commands, for example create_handoff_gist reading from stdin or a file.

---

## Versioning

- This repository uses normal Git history
- Individual skills evolve conservatively
- Backwards-incompatible changes should be avoided or clearly documented

---

## What belongs here (and what does not)

Belongs in toolbox:
- GitHub automation
- handoff capture
- normalization scripts
- repeatable workflow glue

Does not belong here:
- project-specific logic
- exploratory scripts
- system provisioning
- long-running services

---

## Philosophy

If Codex needs to do it more than once, and it has side effects, it belongs in toolbox.

---

## License

Personal use. Adapt as needed.
