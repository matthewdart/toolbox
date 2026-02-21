# chatgpt.extract_markdown

## Description

Extract embedded markdown from a shared ChatGPT Canvas page. Fetches the page HTML, parses the embedded content payload, and returns the markdown text with an optional title.

## Non-goals

- Rendering or reformatting the extracted markdown
- Authentication or session management for private canvases
- Batch processing of multiple canvas URLs

## Deterministic behavior

Given the same canvas URL and the same upstream page content, the extracted title and markdown are deterministic. No hidden prompting or interactive behavior is used.
