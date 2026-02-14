---
name: keychain-secrets
description: Retrieve secrets from the macOS login keychain. Use when a capability or command needs a secret (API key, token, account ID) that isn't already in the environment.
---

# Keychain Secrets

When a capability requires a secret that isn't set in the environment, check the macOS login keychain before asking the user.

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
| Cloudflare | `Global API Key`, `API Token`, `Account ID` |
| OpenAI | `API Key` |
| GitHub | `Classic Personal Access Token`, `Fine-Grained Personal Access Token` |
| Tailscale | `Auth Key` |
| AWS | `Access Key`, `Secret Key` |
| Docker | `Access Token` |

Service names follow the pattern: **`<Provider> <Credential Type>`**

Examples: `Cloudflare Global API Key`, `OpenAI API Key`, `GitHub Classic Personal Access Token`

### Account name (`-a`)

The account identifies **which account or identity** the credential belongs to:

- An email address: `user@example.com`
- A username: `myusername`
- A service/project name: `My Project`
- A descriptive name: `personal`, `work`

### Env var mapping

The env var name is derived from the service name by converting to `SCREAMING_SNAKE_CASE`:

| Service name | Derived env var |
|---|---|
| `Cloudflare API Token` | `CLOUDFLARE_API_TOKEN` |
| `Cloudflare Account ID` | `CLOUDFLARE_ACCOUNT_ID` |
| `OpenAI API Key` | `OPENAI_API_KEY` |
| `Tailscale Auth Key` | `TAILSCALE_AUTH_KEY` |

### Comment field (`-j`) — resolving ambiguity

**Always** store an `env:VAR_NAME` hint in the comment field when:

- The SCREAMING_SNAKE_CASE conversion doesn't match the conventional env var name
- The credential is used with a non-obvious env var name
- Multiple env var names are common for the same credential type

Examples of ambiguity that require a comment:

```bash
# "Global API Key" vs "API Key" vs "API Token" — which CLOUDFLARE_* var?
-j 'env:CLOUDFLARE_API_KEY'

# GitHub tokens can be GITHUB_TOKEN, GH_TOKEN, GHCR_TOKEN depending on use
-j 'env:GHCR_TOKEN'

# Tailscale uses TAILSCALE_AUTHKEY (no underscore) not TAILSCALE_AUTH_KEY
-j 'env:TAILSCALE_AUTHKEY'
```

**Rules:**
- If the comment field contains `env:VAR_NAME`, use that as the env var name
- Otherwise, convert the service name to SCREAMING_SNAKE_CASE
- Never guess — if unsure of the conventional env var name, ask the user

## Example: checking then exporting

```bash
if [ -z "$OPENAI_API_KEY" ]; then
  export OPENAI_API_KEY="$(security find-generic-password -s 'OpenAI API Key' -a 'my-project' -w 2>/dev/null)"
fi
```

## Deriving related values from metadata

Some capabilities need values derived from keychain metadata, not just the password. For example, `CLOUDFLARE_EMAIL` can be read from the account field on a Cloudflare entry:

```bash
if [ -z "$CLOUDFLARE_EMAIL" ]; then
  export CLOUDFLARE_EMAIL="$(security find-generic-password -s 'Cloudflare Global API Key' | grep '"acct"' | sed 's/.*="//;s/"//')"
fi
```

This does **not** trigger an approval prompt since it only reads metadata.

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

| Service name | Account | Env var | Override (`-j`) | Used by |
|---|---|---|---|---|
| `Cloudflare Global API Key` | *(user's email)* | `CLOUDFLARE_API_KEY` | `env:CLOUDFLARE_API_KEY` | `infra.setup_mcp_portal` |
| `Cloudflare Account ID` | *(user's email)* | `CLOUDFLARE_ACCOUNT_ID` | — | `infra.setup_mcp_portal` |
| `OpenAI API Key` | *(project name)* | `OPENAI_API_KEY` | — | `media.analyze_video`, `openai.calculate_usage_cost` |
| `GitHub Classic Personal Access Token` | *(username)* | `GHCR_TOKEN` | `env:GHCR_TOKEN` | `infra.ghcr_push` |

Note: `infra.setup_mcp_portal` also needs `CLOUDFLARE_EMAIL` — derive it from the account field on the `Cloudflare Global API Key` entry (see "Deriving related values" above).

## Notes

- The login keychain is unlocked when you log into your Mac. Reads still prompt for approval because all items are stored with `-T ''` (empty access list).
- Secrets are stored locally only (not synced to iCloud).
- If `security find-generic-password` fails (secret not found), ask the user to provide the value and offer to store it.
- Never use `-T` with an app path when storing — the empty access list is a deliberate security choice.
- Never log, print, or echo secret values. Only retrieve with `-w` when assigning directly to an env var.
