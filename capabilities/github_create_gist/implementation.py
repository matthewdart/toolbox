"""Core capability: create a secret GitHub Gist from files or inline content."""
from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional


class GistError(Exception):
    """Base error for gist creation failures."""


class DependencyError(GistError):
    """Raised when required external dependencies are missing."""


class ValidationError(GistError):
    """Raised when inputs are invalid."""


def _run_gh(args: List[str], input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def create_gist(
    files: Optional[List[str]] = None,
    content: Optional[str] = None,
    filename: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a secret GitHub Gist and return the gist URL.

    Either provide file paths via `files`, or inline text via `content`.
    """
    if not shutil.which("gh"):
        raise DependencyError("gh not found in PATH")

    file_list = files or []

    if filename and file_list:
        raise ValidationError("filename is only valid when using content (not files)")

    if not file_list and not content:
        raise ValidationError("provide either files or content")

    cmd = ["gh", "gist", "create"]
    if description:
        cmd += ["-d", description]

    if file_list:
        cmd += file_list
        result = _run_gh(cmd)
    else:
        cmd.append("-")
        if filename:
            cmd += ["-f", filename]
        result = _run_gh(cmd, input_text=content)

    if result.returncode != 0:
        message = result.stderr.strip() or "gh gist create failed"
        raise GistError(message)

    gist_url = result.stdout.strip()

    return {
        "gist_url": gist_url,
    }
