---
name: keychain-secrets
description: Retrieve secrets from the macOS login keychain. Use when a capability or command needs a secret (API key, token, password) that isn't already in the environment.
---

# Keychain Secrets

When a capability requires a secret that isn't set in the environment, check the macOS login keychain before asking the user.

## What belongs in the keychain

Only store **actual secrets** — values that grant access or authenticate:

- API keys and tokens
- Passwords and auth keys
- Private keys and client secrets

**Do not store** non-secret configuration values like account IDs, email addresses, project names, or URLs. These should be passed as capability inputs, stored in config files, or derived from keychain metadata (see "Deriving related values" below).

## Retrieving a secret

```bash
export ENV_VAR_NAME="$(security find-generic-password -s 'Service Name' -a 'account' -w)"
```

The `-w` flag outputs only the password. This triggers a macOS approval prompt every time (secrets are stored with an empty access list).

## Reading metadata (no approval prompt)

Reading the account or comment field does **not** trigger an approval prompt and does **not** expose the secret value:

```bash
# Read the account field (e.g. to get an email address)
security find-generic-password -s 'Service Name' | grep '"acct"' | sed 's/.*="//;s/"//'

# Read the comment field (e.g. to get the env var override)
security find-generic-password -s 'Service Name' | grep '"icmt"' | sed 's/.*="//;s/"//'
```

## Storing a secret

```bash
security add-generic-password -s 'Service Name' -a 'account' -w 'secret-value' -j 'env:ENV_VAR_NAME' -T '' -U
```

- `-T ''` = empty access list — **every read triggers a macOS approval prompt**, even from Terminal. This is intentional: the owner wants OS-level approval before any secret is accessed, regardless of Claude's permission mode.
- `-U` = update the entry if it already exists.
- `-j` = comment field — **always populate** with `env:VAR_NAME` when there is any ambiguity about the env var mapping (see below).

## Listing secrets (safe — never exposes values)

To find keychain entries by service name pattern, use metadata-only queries. **Never use `-w` when listing or searching.**

```bash
# List all entries matching a service name pattern (no passwords exposed)
security dump-keychain | grep '"svce"' | sort -u

# Find a specific entry's metadata
security find-generic-password -s 'Service Name'
```

The metadata output includes `svce` (service), `acct` (account), and `icmt` (comment) but **not** the password.

## Naming Conventions

### Service name (`-s`)

The service name describes **what the credential is** in human-readable Title Case. Use the provider's own terminology for the credential type.

Common patterns:

| Provider | Credential types |
|---|---|
| Cloudflare | `Global API Key`, `API Token` |
| OpenAI | `API Key` |
| GitHub | `Classic Personal Access Token`, `Fine-Grained Personal Access Token` |
| Tailscale | `Auth Key` |
| AWS | `Access Key`, `Secret Key` |
| Docker | `Access Token` |

Service names follow the pattern: **`<Provider> <Credential Type>`**

Examples: `Cloudflare Global API Key`, `OpenAI API Key`, `GitHub Classic Personal Access Token`

### Account name (`-a`)

The account field identifies **which account or identity** the credential belongs to. Use the most useful identifier for the context — this may also serve as a non-secret config value that capabilities need alongside the secret:

- An account ID: `538fc7...` (e.g. Cloudflare account ID needed as `CLOUDFLARE_ACCOUNT_ID`)
- An email address: `user@example.com`
- A username: `myusername`
- A service/project name: `My Project`

When the account field carries a value that maps to an env var, document the mapping in the comment field (see below).

### Env var mapping

The env var name is derived from the service name by converting to `SCREAMING_SNAKE_CASE`:

| Service name | Derived env var |
|---|---|
| `Cloudflare API Token` | `CLOUDFLARE_API_TOKEN` |
| `OpenAI API Key` | `OPENAI_API_KEY` |
| `Tailscale Auth Key` | `TAILSCALE_AUTH_KEY` |

### Comment field (`-j`) — hints and metadata mappings

The comment field documents how to map keychain fields to env vars. It supports multiple space-separated hints:

- `env:VAR_NAME` — the env var for the **password** (overrides SCREAMING_SNAKE_CASE)
- `acct:VAR_NAME` — the env var for the **account field**
- `email:VALUE` — an associated email address (useful when the account field holds something else)

**Always** populate the comment field when:

- The SCREAMING_SNAKE_CASE conversion doesn't match the conventional env var name
- The account field carries a value that maps to an env var
- Additional non-secret config values are associated with this credential
- Multiple env var names are common for the same credential type

Examples:

```bash
# Cloudflare: password → CLOUDFLARE_API_KEY, account field → CLOUDFLARE_ACCOUNT_ID, email for CLOUDFLARE_EMAIL
-j 'env:CLOUDFLARE_API_KEY acct:CLOUDFLARE_ACCOUNT_ID email:user@example.com'

# GitHub tokens can be GITHUB_TOKEN, GH_TOKEN, GHCR_TOKEN depending on use
-j 'env:GHCR_TOKEN'

# Tailscale uses TAILSCALE_AUTHKEY (no underscore) not TAILSCALE_AUTH_KEY
-j 'env:TAILSCALE_AUTHKEY'
```

**Rules for resolving env var names:**
- `env:VAR_NAME` in the comment → use that for the password
- `acct:VAR_NAME` in the comment → export the account field as that env var
- `email:VALUE` in the comment → export that value as `*_EMAIL` (e.g. `CLOUDFLARE_EMAIL`)
- No comment → convert the service name to SCREAMING_SNAKE_CASE
- Never guess — if unsure of the conventional env var name, ask the user

## Example: checking then exporting

```bash
if [ -z "$OPENAI_API_KEY" ]; then
  export OPENAI_API_KEY="$(security find-generic-password -s 'OpenAI API Key' -a 'my-project' -w 2>/dev/null)"
fi
```

## Deriving related values from metadata

Some capabilities need non-secret config values alongside the secret. These can be derived from keychain metadata **without triggering an approval prompt**.

Read the comment field first to discover what mappings are available:

```bash
# Read the comment to see all hints
security find-generic-password -s 'Cloudflare Global API Key' | grep '"icmt"' | sed 's/.*="//;s/"//'
# → env:CLOUDFLARE_API_KEY acct:CLOUDFLARE_ACCOUNT_ID email:user@example.com
```

Then export the mapped values:

```bash
# acct: hint → export account field as CLOUDFLARE_ACCOUNT_ID (no approval prompt)
if [ -z "$CLOUDFLARE_ACCOUNT_ID" ]; then
  export CLOUDFLARE_ACCOUNT_ID="$(security find-generic-password -s 'Cloudflare Global API Key' | grep '"acct"' | sed 's/.*="//;s/"//')"
fi

# email: hint → export the email value as CLOUDFLARE_EMAIL (no approval prompt)
if [ -z "$CLOUDFLARE_EMAIL" ]; then
  export CLOUDFLARE_EMAIL="$(security find-generic-password -s 'Cloudflare Global API Key' | grep '"icmt"' | sed 's/.*email://;s/ .*//')"
fi
```

These reads are safe — they only access metadata, not the secret value.

## Finding the right keychain item

When looking for a secret, search by service name pattern. **Never use `-w` during search.**

1. Check if the env var is already set — if so, skip
2. Search metadata for matching service names (use provider name as search term)
3. Read the comment field to confirm the env var mapping
4. Only then retrieve the password with `-w` (triggers approval)

```bash
# Step 1: check environment
[ -n "$CLOUDFLARE_API_KEY" ] && echo "Already set" && return

# Step 2: find matching entries (no password exposed)
security find-generic-password -s 'Cloudflare Global API Key' 2>/dev/null | grep -E '"(svce|acct|icmt)"'

# Step 3: confirm the env var mapping from comment
# icmt should show env:CLOUDFLARE_API_KEY

# Step 4: retrieve (triggers OS prompt)
export CLOUDFLARE_API_KEY="$(security find-generic-password -s 'Cloudflare Global API Key' -w)"
```

## Known secrets

| Service name | Account | Env var | Comment (`-j`) | Used by |
|---|---|---|---|---|
| `Cloudflare Global API Key` | *(account ID)* | `CLOUDFLARE_API_KEY` | `env:CLOUDFLARE_API_KEY acct:CLOUDFLARE_ACCOUNT_ID email:...` | `infra.setup_mcp_portal` |
| `OpenAI API Key` | *(project name)* | `OPENAI_API_KEY` | — | `media.analyze_video`, `openai.calculate_usage_cost` |
| `GitHub Classic Personal Access Token` | *(username)* | `GHCR_TOKEN` | `env:GHCR_TOKEN` | `infra.ghcr_push` |

Note: `infra.setup_mcp_portal` also needs `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_EMAIL`. These are not secrets — derive them from the `Cloudflare Global API Key` entry's metadata using the `acct:` and `email:` hints (see "Deriving related values" above).

## Notes

- The login keychain is unlocked when you log into your Mac. Reads still prompt for approval because all items are stored with `-T ''` (empty access list).
- Secrets are stored locally only (not synced to iCloud).
- If `security find-generic-password` fails (secret not found), ask the user to provide the value and offer to store it.
- Never use `-T` with an app path when storing — the empty access list is a deliberate security choice.
- Never log, print, or echo secret values. Only retrieve with `-w` when assigning directly to an env var.
