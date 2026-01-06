---
name: canvas-markdown
description: Extract markdown from ChatGPT Canvas shared URLs. Use when asked to turn a canvas/shared link into markdown or save it to a file.
---

# Canvas Markdown

Use the bundled script to fetch a shared canvas page and extract the embedded markdown.

## Run

- Run `scripts/canvas_markdown.py <url>` to print markdown to stdout.
- Pipe a URL on stdin if no argument is provided.
- Pass `-o <path>` to write the markdown to a file.

## Notes

- Require network access and `curl` in PATH.
- Fail fast if the page does not contain an embedded `content` field.
