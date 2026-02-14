# Owner Preferences — Cross-Repo Conventions and Patterns

This document captures the owner's established patterns, conventions, and tool preferences. Agents should treat these as strong defaults when working in any repository in the ecosystem.

These are **observed and confirmed patterns**, not aspirational standards. Deviations are allowed when a project's needs demand it, but should be conscious choices, not accidental drift.

---

## Communication and Interaction

- Be concise and direct. No verbose introductions or "welcome to" language.
- State assumptions and understanding before implementing.
- Explain trade-offs when multiple approaches exist.
- Point out edge cases and side effects proactively.
- Propose before implementing when execution risk is non-trivial.
- For complex or multi-file changes, analyse and plan before writing code.

---

## Python Conventions

All Python repositories follow these conventions unless explicitly overridden:

- `from __future__ import annotations` at the top of every Python file, without exception
- Type hints on all function signatures and return types
- `pathlib.Path` as the universal path type — no raw string path manipulation
- `dataclasses` preferred for structured data (`@dataclass`, `@dataclass(frozen=True)`)
- `Protocol` for interfaces — not abstract base classes
- Private functions prefixed with underscore (`_helper_name`)
- Module-level constants in `UPPER_SNAKE_CASE`
- Custom exception hierarchies per module when error semantics matter
- Docstrings are brief one-liners on public API functions; not required on internal helpers
- Import ordering: stdlib, then third-party, then local
- Modern type syntax preferred: `dict[str, Any]`, `list[str]`, `X | None` over `Dict`, `List`, `Optional`

### Python build and tooling

- `pyproject.toml` with `setuptools` backend — not poetry, hatch, or flit
- `src/` layout (`[tool.setuptools.packages.find] where = ["src"]`)
- `pip install -e .` for development
- `pytest` for testing — `test_` prefix functions, `tmp_path` fixtures, `conftest.py` for shared fixtures
- No linters or formatters are configured (no ruff, black, flake8, isort, mypy). Code style is maintained by convention and review.

---

## TypeScript Conventions

- `strict: true` in tsconfig.json
- Interfaces preferred over types for object shapes
- camelCase for variables/functions, PascalCase for interfaces/types
- `vitest` for testing (not Jest) — `describe`/`it` BDD style, `.test.ts` suffix
- `npm` as package manager (not pnpm or yarn)

---

## SQL Conventions

- SQL views are the primary modelling surface — prefer SQL refactors over Python refactors
- No ORM — raw SQL and DuckDB views
- SQL models numbered and executed in order (`00_sources.sql`, `10_records_enriched.sql`)

---

## Documentation and Markdown

- H1 for document title, H2 for major sections
- Horizontal rules (`---`) as section separators in governance docs
- Bullet points with `-` (not `*`)
- Code blocks with language tags (```bash, ```yaml, ```python)
- Bold (`**keyword**`) for emphasis, not ALL CAPS
- Direct, terse prose — no filler paragraphs
- README structure: title, one-line description, quickstart, commands, architecture

---

## Git and Version Control

- Commit messages: lowercase, imperative mood, under 72 characters
- Short, descriptive single-line messages
- No issue numbers in commit messages (connections managed via PRs)
- Conventional Commits prefixes (`fix:`, `feat:`, `ci:`) are used but not enforced

---

## Naming Conventions

- Repository names: lowercase, hyphenated (`remarkable-pipeline`, `archi-mcp-bridge`)
- Python packages: lowercase, underscored (`remarkable_pipeline`)
- Python files: lowercase, underscored (`sql_safety.py`)
- Docker container/image names match repo names
- GHCR images at `ghcr.io/matthewdart/<name>`

---

## Infrastructure Defaults

- Docker multi-stage builds with `python:3.11-slim` base for Python services
- Docker Compose with Cloudflare Tunnel sidecar for deployment
- GHCR for container images
- ARM64 (`linux/arm64`) as primary deployment target
- Oracle Cloud VM as hosting platform
- Tailscale for SSH connectivity
- GitHub Actions for CI/CD, with reusable workflows in toolbox
- No Kubernetes — Docker Compose everywhere
- No Terraform/IaC — manual VM setup with shell scripts

---

## Integration Patterns

- MCP (Model Context Protocol) as the primary agent integration surface
- `CONTRACT.md` or `SPEC.md` as authoritative project specification per repo
- `PLAN.md` for tracking work progress in small repos
- `docs/plans/` for structured plan documents in Tier 2 repos

---

## Explicit Non-Preferences

The following are deliberately not used. Do not introduce them without explicit request:

- Linters or formatters (ruff, black, flake8, pylint, isort, mypy)
- `.editorconfig` files
- Pre-commit hooks
- Monorepo tools (nx, turborepo, lerna)
- ORMs (SQLAlchemy, Django ORM, etc.)
- Dependency lock files
- Kubernetes
- Terraform or IaC tools
- Abstract base classes in Python (use Protocol)
- Logging frameworks (minimal/print-based logging)
