---
name: create-private-gist
description: Create a private GitHub Gist from files or stdin using gh. Use when asked to create a private/secret gist or upload text to a gist.
---

# Create Private Gist

Use the bundled script to create a private (secret) gist via the GitHub CLI.

## Run

- Run `scripts/create_private_gist.py <file> [<file> ...]` to create a gist from files.
- Pipe content on stdin when no files are provided.
- Use `-f <name>` to set a filename for stdin.
- Use `-d <desc>` to set a gist description.

## Notes

- Require `gh` in PATH and an authenticated session.
- Never pass `--public`; this skill always creates secret gists.
