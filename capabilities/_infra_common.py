"""Shared infrastructure helpers for local subprocess execution."""
from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List, Optional


class InfraError(Exception):
    """Base error for infrastructure capability failures."""


class DependencyError(InfraError):
    """Raised when required external dependencies are missing."""


class ComposeError(InfraError):
    """Raised when docker compose fails."""


def run_cmd(
    cmd: List[str],
    *,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """Execute a command locally as a subprocess."""
    full_env = None
    if env:
        full_env = dict(os.environ)
        full_env.update(env)
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        env=full_env,
        timeout=timeout,
    )


def run_shell(
    script: str,
    *,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """Execute a shell script via sh -c."""
    return subprocess.run(
        ["sh", "-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=timeout,
    )
