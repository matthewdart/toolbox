# text.normalize_markdown

## Description

Normalize Markdown text by trimming trailing whitespace and ensuring a final newline based on options. Returns the normalized text and a list of applied changes.

## Non-goals

- Markdown parsing or AST transformations
- Reformatting headings, lists, or code blocks
- Linting or style enforcement beyond whitespace handling

## Deterministic behavior

Given the same input text and options, the output text and `changes` list are deterministic. No external dependencies or hidden prompts are used.
