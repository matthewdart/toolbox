---
name: export-cookies
description: Export browser cookies for a domain to a Netscape cookies.txt file using yt-dlp cookie extraction. Useful for login-gated downloads.
---

# Export Cookies

Export browser cookies for a domain to a Netscape cookies.txt file using yt-dlp cookie extraction. Useful for login-gated downloads.

## Invocation

Call the `browser.export_cookies` capability via MCP:

```
browser.export_cookies(domain="...", output="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `browser` | string | no | `"safari"` | Browser name (e.g., safari, chrome, firefox). |
| `domain` | string | yes | — | Domain to export cookies for (e.g. brighttalk.com). |
| `output` | string | yes | — | Output path for the cookies.txt file. |
| `profile` | string? | no | — | Optional browser profile name or path. |
| `container` | string? | no | — | Firefox container name (ignored by non-Firefox browsers). |
| `keyring` | string? | no | — | Chromium keyring (primarily for Linux). Usually not needed on macOS. |
| `include_subdomains` | boolean | no | `true` | Include cookies for subdomains of the target domain. |
| `quiet` | boolean | no | `false` | Reduce stderr logging. |

## Error Codes

| Code | Description |
|------|-------------|
| `dependency_error` | yt-dlp is not installed. |
| `extraction_error` | Failed to extract cookies from the browser (permissions, profile not found, etc.). |
| `validation_error` | Input did not match schema. |

## Side Effects

Reads the browser cookie store and writes a Netscape-format cookies.txt file to the specified output path. Treat the output file like a credential.
