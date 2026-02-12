# gist.create_private

## Description

Create a secret (private) GitHub Gist from one or more files or inline text content using the GitHub CLI (`gh`).

## Non-goals

- Creating public gists
- Updating or deleting existing gists
- Listing or searching gists
- Managing gist comments

## Deterministic behavior

Given the same input files or content, the capability creates a gist with the same content. The returned URL will differ on each invocation as a new gist is created each time.
