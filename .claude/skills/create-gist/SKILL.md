---
name: create-gist
description: Create a private GitHub gist from files or content. Use when asked to create a gist, share a snippet, or capture content as a gist.
---

# Create Private Gist

Create a secret GitHub gist using the `gh` CLI.

## Quick Reference

The `gist.create_private` capability handles this programmatically via the MCP server. For direct use:

```bash
# From files
gh gist create --secret file1.py file2.md

# From stdin
echo "content" | gh gist create --secret -f snippet.txt

# With description
gh gist create --secret -d "Description here" file.py
```

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status` to verify)
- Never prompt for credentials or run `gh auth login`

## Notes

- Always use `--secret` (not `--public`) unless explicitly asked for public
- The gist URL is printed to stdout on success
- Multiple files can be included in a single gist
