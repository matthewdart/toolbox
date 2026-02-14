"""Core capability: build a Docker image and push it to GHCR."""
from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List


class GHCRPushError(Exception):
    """Base error for ghcr-push failures."""


class DependencyError(GHCRPushError):
    """Raised when required external dependencies are missing."""


class BuildPushError(GHCRPushError):
    """Raised when the docker buildx build --push command fails."""


def _build_docker_cmd(
    repo: str,
    context: str,
    dockerfile: str,
    platform: str,
    tags: List[str],
) -> List[str]:
    """Construct the docker buildx build command list."""
    image_base = f"ghcr.io/{repo}"
    cmd = ["docker", "buildx", "build", "--platform", platform, "-f", dockerfile]
    for tag in tags:
        cmd += ["-t", f"{image_base}:{tag}"]
    cmd += ["--push", context]
    return cmd


def _run_docker(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    """Execute a docker command and return the completed process."""
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def ghcr_push(
    repo: str,
    context: str,
    dockerfile: str = "Dockerfile",
    platform: str = "linux/arm64",
    tags: List[str] | None = None,
    dry_run: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build a Docker image for a specified platform and push it to GHCR.

    Returns a dict describing the action taken and its outcome.
    Raises DependencyError if docker is not available.
    Raises BuildPushError if the docker command fails with a non-zero exit code.
    """
    if not shutil.which("docker"):
        raise DependencyError("docker not found in PATH")

    effective_tags = tags if tags is not None else ["latest"]
    image_base = f"ghcr.io/{repo}"
    cmd = _build_docker_cmd(repo, context, dockerfile, platform, effective_tags)

    if dry_run:
        return {
            "image": image_base,
            "tags": effective_tags,
            "platform": platform,
            "action": "dry_run",
            "docker_command": cmd,
        }

    proc = _run_docker(cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "docker buildx build failed"
        raise BuildPushError(error_msg)

    return {
        "image": image_base,
        "tags": effective_tags,
        "platform": platform,
        "action": "pushed",
    }
