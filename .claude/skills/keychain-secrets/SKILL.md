---
name: keychain-secrets
description: Retrieve secrets from the macOS login keychain. Use when a capability or command needs a secret (API key, token, account ID) that isn't already in the environment.
---

# Keychain Secrets

When a capability requires a secret that isn't set in the environment, check the macOS login keychain before asking the user.

## Retrieving a secret

```bash
export ENV_VAR_NAME="$(security find-generic-password -s 'service-name' -a 'account-name' -w)"
```

The `-w` flag outputs only the password. This may trigger a macOS approval prompt (password or Touch ID) on first access.

## Storing a secret

```bash
security add-generic-password -s 'service-name' -a 'account-name' -w 'secret-value' -T '' -U
```

- `-T ''` = empty access list — **every read triggers a macOS approval prompt**, even from Terminal. This is intentional: the owner wants OS-level approval before any secret is accessed, regardless of Claude's permission mode.
- `-U` = update the entry if it already exists.

## Conventions

- Service name: use the env var name (e.g. `CLOUDFLARE_API_TOKEN`, `OPENAI_API_KEY`)
- Account name: use `toolbox`
- Always check `$ENV_VAR` first — only read from keychain if the var is unset
- Never use `-T` with an app path when storing — the empty access list is a deliberate security choice

## Example: checking then exporting

```bash
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
  export CLOUDFLARE_API_TOKEN="$(security find-generic-password -s 'CLOUDFLARE_API_TOKEN' -a 'toolbox' -w 2>/dev/null)"
fi
```

## Known secrets

| Env var | Service name | Used by |
|---------|-------------|---------|
| `CLOUDFLARE_API_TOKEN` | `CLOUDFLARE_API_TOKEN` | `infra.setup_mcp_portal` |
| `CLOUDFLARE_ACCOUNT_ID` | `CLOUDFLARE_ACCOUNT_ID` | `infra.setup_mcp_portal` |
| `OPENAI_API_KEY` | `OPENAI_API_KEY` | `media.analyze_video`, `openai.calculate_usage_cost` |
| `GHCR_TOKEN` | `GHCR_TOKEN` | `infra.ghcr_push` |

## Notes

- The login keychain is unlocked when you log into your Mac. Reads may still prompt for approval depending on the item's access control settings.
- Secrets are stored locally only (not synced to iCloud).
- If `security find-generic-password` fails (secret not found), ask the user to provide the value and offer to store it.
