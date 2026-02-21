"""Core capability: extract markdown from a ChatGPT Canvas shared URL."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import unicodedata
from typing import Any, Dict, Optional, Tuple


class CanvasExtractionError(Exception):
    """Base error for canvas extraction failures."""


class DependencyError(CanvasExtractionError):
    """Raised when required external dependencies are missing."""


class NetworkError(CanvasExtractionError):
    """Raised for network or HTTP failures."""


class ParseError(CanvasExtractionError):
    """Raised when the canvas page cannot be parsed."""


DEFAULT_BASENAME = "canvas"


def _fetch_html(url: str) -> str:
    curl = shutil.which("curl")
    if not curl:
        raise DependencyError("curl not found in PATH")

    result = subprocess.run(
        [curl, "-fsSL", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "curl failed"
        raise NetworkError(message)
    return result.stdout


def _extract_payload(html: str) -> Tuple[Optional[str], str]:
    pattern = re.compile(r'streamController\.enqueue\("((?:\\.|[^"\\])*)"\);')
    for match in pattern.finditer(html):
        js_string = match.group(1)
        try:
            decoded = json.loads(f'"{js_string}"')
        except json.JSONDecodeError:
            continue
        try:
            data = json.loads(decoded)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, list):
            continue
        title = None
        try:
            title_idx = data.index("title")
        except ValueError:
            title_idx = None
        if title_idx is not None and title_idx + 1 < len(data):
            title = data[title_idx + 1]
        try:
            content_idx = data.index("content")
        except ValueError:
            continue
        if content_idx + 1 < len(data):
            return title, data[content_idx + 1]
    raise ParseError("markdown content not found in canvas payload")


def _slugify_title(title: Optional[str]) -> str:
    if not title:
        return DEFAULT_BASENAME
    normalized = unicodedata.normalize("NFKD", title)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text or DEFAULT_BASENAME


def _suggest_filename(title: Optional[str]) -> str:
    return f"{_slugify_title(title)}.md"


def _resolve_output_path(output_arg: str, title: Optional[str]) -> str:
    if output_arg == "auto":
        return _suggest_filename(title)
    if output_arg.endswith(os.sep) and not os.path.isdir(output_arg):
        raise CanvasExtractionError(f"output directory not found: {output_arg}")
    if os.path.isdir(output_arg):
        return os.path.join(output_arg, _suggest_filename(title))
    return output_arg


def extract_markdown(
    url: str,
    output: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract markdown from a ChatGPT Canvas shared URL.

    Returns a dict with title, markdown content, suggested_filename,
    and optionally an output_path if output was specified.
    """
    if not url or not str(url).strip():
        raise CanvasExtractionError("url is required")

    html = _fetch_html(url)
    title, markdown = _extract_payload(html)
    suggested = _suggest_filename(title)

    result: Dict[str, Any] = {
        "title": title,
        "markdown": markdown,
        "suggested_filename": suggested,
        "output_path": None,
    }

    if output:
        output_path = _resolve_output_path(output, title)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(markdown)
        result["output_path"] = output_path

    return result
