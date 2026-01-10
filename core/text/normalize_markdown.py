"""Core capability: normalize Markdown text."""
from __future__ import annotations

from typing import Dict, List


class NormalizeMarkdownError(Exception):
    """Raised when normalization inputs are invalid."""


def normalize_markdown(text: str, options: Dict[str, bool] | None = None) -> Dict[str, object]:
    if not isinstance(text, str):
        raise NormalizeMarkdownError("text must be a string")

    opts = options or {}
    trim_trailing_whitespace = bool(opts.get("trim_trailing_whitespace", True))
    ensure_final_newline = bool(opts.get("ensure_final_newline", True))

    changes: List[str] = []
    normalized = text

    if trim_trailing_whitespace:
        lines = normalized.splitlines()
        trimmed_lines = [line.rstrip() for line in lines]
        if trimmed_lines != lines:
            changes.append("trim_trailing_whitespace")
        normalized = "\n".join(trimmed_lines)

    if ensure_final_newline:
        if normalized and not normalized.endswith("\n"):
            normalized = normalized + "\n"
            changes.append("ensure_final_newline")
        elif normalized == "":
            # Empty input becomes a single newline to satisfy final newline rule.
            normalized = "\n"
            changes.append("ensure_final_newline")

    return {"text": normalized, "changes": changes}
