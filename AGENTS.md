# AGENTS.md — Shared Agent Safety Rules

These rules apply to all repositories in the ecosystem. They are loaded via `@vendor/handbook/AGENTS.md` from each repo's AGENTS.md.

Repo-specific rules (source of truth, non-negotiable rules, workflow, architecture, commands) remain in each repo's own AGENTS.md.

---

## Deployment and Infrastructure Safety

These rules apply whenever an agent modifies, deploys to, or configures a running service or infrastructure component. They are **non-negotiable** — not "best practice," not "recommended."

### Verify state before acting

Before modifying any system (remote or local), verify its current state. Do not extrapolate from assumptions, documentation, or what another system looks like.

- SSH in and check. Read the actual config files. Query the actual API.
- When two things must be consistent (e.g., backend and renderer, tunnel hostname and DNS, docker-compose env and .env), verify BOTH sides before changing either.
- When changing a default in one location, search for all other locations that set the same default and update them together.

### Verify outcome after acting

Verification means confirming the system is in the desired state, not that the command exited 0.

After deploying a container:

1. `docker ps` — confirm it is running (not restarting)
2. `docker logs <container> --tail 20` — confirm no crash/error output
3. Hit the health endpoint — confirm a non-error response
4. If the service has an MCP endpoint, send a test request

After modifying a Cloudflare tunnel, DNS record, or portal config:

1. Verify via the Cloudflare API (not just that the PUT succeeded)
2. Test the public URL end-to-end

After pushing a CI/CD change:

1. Watch the GitHub Actions run to completion
2. If the workflow deploys, verify the deployment (not just the workflow)

### Never deploy untested assumptions about external systems

If you are unsure how an external system behaves (MCP SDK internals, Starlette lifespan propagation, Cloudflare tunnel routing, Docker memory limits), **research it before committing to an approach**.

Acceptable research:

- Read the library source code
- Read the official documentation
- Write a minimal local test
- Ask the user

Not acceptable: assume based on general knowledge, push to main, discover you were wrong.

---

## Docker and CI/CD Preflight

Before pushing any Dockerfile, docker-compose.yml, override template, or GitHub Actions workflow, complete the applicable checks below. These exist because every item has caused a real deployment failure.

### GitHub Actions prerequisites

- **Repo workflow permissions**: `gh api repos/{owner}/{repo}/actions/permissions/workflow` — confirm `default_workflow_permissions` includes `write` if the workflow pushes to GHCR. If not, add an explicit `permissions:` block to the calling workflow.
- **Repo secrets**: `gh secret list -R {owner}/{repo}` — confirm every secret referenced in the workflow and override template is configured. Do not push a deploy workflow that references `TS_AUTHKEY`, `CF_TUNNEL_TOKEN`, or `HTTP_BEARER_TOKEN` to a repo that has zero secrets.
- **Dockerfile path**: if the build context is not `.`, explicitly set the `dockerfile` input on the reusable workflow. The shared `build-arm-image.yml` resolves `dockerfile` relative to the **repo root**, not the build context.

### Override template and envsubst

The `deploy-stack.yml` workflow runs `envsubst` on the override template. This replaces **all** `${VAR}` patterns — including variables you intended to come from `.env` on the VM.

- Every `${VAR}` in the override template **must** exist in `deploy-stack.yml`'s `env:` block. If the variable is not listed there, `envsubst` silently replaces it with an empty string.
- Variables that should come from the VM's `.env` file must **not** appear in the override template. Put them in `docker-compose.yml` using bare names (e.g., `- GITHUB_CLIENT_ID`) so Compose reads them from `.env` at runtime.
- When adding a new secret to an override template, check whether `deploy-stack.yml` already lists it. If not, the shared workflow must be updated first.

### Dockerfile runtime

- **Non-root user**: if the Dockerfile creates a non-root user or if `docker-compose.yml` overrides the UID with `user:`, verify:
  - The home directory exists (`useradd -m` or explicit `mkdir`)
  - `HOME` is explicitly set in `environment:` if the UID has no `/etc/passwd` entry
  - `PATH` includes venv or tool directories (e.g., `ENV PATH="/app/.venv/bin:$PATH"`)
- **System dependencies**: if a Python/Node package depends on a system binary (Inkscape, curl, ffmpeg, docker CLI), verify the binary is installed in the image. Do not assume pip/npm packages are self-contained.
- **Path resolution**: code that uses `Path(__file__).parent` or similar will resolve to the **site-packages** directory inside a container, not the application root. Verify all path resolution logic against the actual container filesystem layout.
- **Resource limits**: only set `memory:` and `cpus:` limits based on measured usage. If you do not know the peak memory of the workload, do not guess — omit the limit or ask the user.

### Docker Compose consistency

- **network_mode**: if a service uses `network_mode: service:<other>`, the referenced service must exist and must not have a profile that prevents it from starting.
- **profiles**: if a service has a `profiles:` key, it will **not** start with `docker compose up -d` unless the profile is explicitly activated via `--profile` or `COMPOSE_PROFILES`. Verify the deploy workflow activates required profiles, or remove the profile from services that must always run.
- **`docker compose -f`**: the explicit `-f` flag disables automatic discovery of `docker-compose.override.yml`. Always use `cd /opt/<service> && docker compose up -d` instead.
- **depends_on**: if service A depends on service B, service B must not be profile-gated unless service A is also gated behind the same profile.

### Cross-service consistency

When a change affects the contract between services (labels, env var names, ports), verify both sides:

- Docker labels read by a discovery system must use the exact key names the consumer expects
- Port numbers must match between the app's `HTTP_PORT`, the compose `ports:` mapping, the cloudflared tunnel routing, and the workflow's `health_port` input
- Container names must match any references in other compose files, tunnel configs, or monitoring

---

## Scope Discipline

- After fixing a bug, do not start a related refactor without asking.
- After an audit or analysis, do not start implementing fixes without asking.
- If a session has consumed one context continuation, treat any further scope expansion as requiring explicit user approval.
- Commit working intermediate progress before starting the next piece of work. Do not treat a multi-step session as a single atomic operation.

### Intermediate commits

Commit what you have before moving on when:

- The current fix works but you see additional improvements to make
- The session has been running for more than 30 minutes of active implementation
- You are about to touch a second repository
- You are about to make a change that depends on the previous change being deployed

---

## Destructive Operations

The following require explicit announcement of their specific effects before execution:

- `git push --force` to any branch
- `rm -rf` on any directory
- Deploying to a running production service while CI/CD may also be deploying
- Overwriting or deleting keychain entries
- Deleting GitHub secrets, repos, or branches
- Making a repository private or changing its visibility
- Any operation that cannot be undone with a single `git checkout` or `docker compose down`

---

## Test Integrity

When a test fails due to your changes, investigate whether the new behaviour is correct before updating the test assertion. Weakening a test to accept new output is not a fix — it hides the question "is this new output actually right?"

- If the new output is correct: update the assertion AND add structural checks (types, required keys, value ranges)
- If the new output is wrong: fix the code, not the test
- Never reduce assertion specificity to make a test pass (e.g., changing `== {"status": "ok"}` to `"status" in response`)

---

## Ambiguity

If you are not sure what the user is asking, **ask for clarification**. Do not interpret an ambiguous statement, implement against your interpretation, and discover you were wrong after the work is done. The cost of one clarifying question is always less than the cost of a reversal.

### Questions are not directives

When a user asks "why is X configured this way?" or "what does Y do?", they are asking for an explanation — not requesting that you change X or remove Y. Answer the question. Do not start implementing changes unless the user explicitly asks for a change after hearing the explanation.
