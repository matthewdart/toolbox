"""Core capability: preflight check for VM deployment readiness."""
from __future__ import annotations

import shutil
import subprocess
from typing import Any, Callable, Dict, List, Optional

SSH_BATCH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]

DEFAULT_COMPOSE_DIRS = [
    "/opt/remarkable-pipeline",
    "/opt/health-ledger",
    "/opt/archi-mcp-bridge",
]


class VmBootstrapError(Exception):
    """Base error for vm-bootstrap failures."""


class DependencyError(VmBootstrapError):
    """Raised when required external dependencies are missing."""


def _run_ssh(host: str, remote_cmd: str) -> subprocess.CompletedProcess[str]:
    """Execute a command on the remote host over SSH."""
    return subprocess.run(
        ["ssh", *SSH_BATCH_OPTIONS, host, remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _check(
    host: str,
    name: str,
    remote_cmd: str,
    validate: Optional[Callable[[str], bool]] = None,
    hint: str = "",
) -> Dict[str, Any]:
    """Run a single preflight check via SSH and return a result dict."""
    proc = _run_ssh(host, remote_cmd)
    stdout = proc.stdout.strip()

    result: Dict[str, Any] = {"check": name, "status": "ok", "detail": stdout}
    if hint:
        result["hint"] = hint

    if proc.returncode != 0:
        result["status"] = "fail"
        result["detail"] = proc.stderr.strip() or "command failed"
        return result

    if validate and not validate(stdout):
        result["status"] = "fail"
        return result

    return result


def bootstrap_vm(
    host: str,
    compose_dirs: Optional[List[str]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run preflight checks for VM deployment readiness.

    Returns a dict summarising which checks passed and which failed.
    Raises DependencyError if ssh is not available.
    """
    if not shutil.which("ssh"):
        raise DependencyError("ssh not found in PATH")

    effective_dirs: List[str] = compose_dirs if compose_dirs is not None else list(DEFAULT_COMPOSE_DIRS)

    checks: List[Dict[str, Any]] = []

    # 1. Docker installed
    checks.append(_check(
        host, "docker", "docker --version",
        hint="Install Docker: https://docs.docker.com/engine/install/ubuntu/",
    ))

    # 2. Docker Compose plugin
    checks.append(_check(
        host, "compose", "docker compose version",
        hint="Install Docker Compose plugin",
    ))

    # 3. Architecture
    checks.append(_check(
        host, "arch", "uname -m",
        validate=lambda out: "aarch64" in out or "arm64" in out,
        hint="Expected ARM64 architecture",
    ))

    # 4. GHCR authentication
    checks.append(_check(
        host, "ghcr",
        'python3 -c "import json; d=json.load(open(\\"/home/ubuntu/.docker/config.json\\")); '
        'print(\\"authenticated\\" if \\"ghcr.io\\" in d.get(\\"auths\\",{}) else \\"unauthenticated\\")" '
        "2>/dev/null || echo unauthenticated",
        validate=lambda out: out.strip() == "authenticated",
        hint="Authenticate: echo $GHCR_TOKEN | docker login ghcr.io -u <user> --password-stdin",
    ))

    # 5. Tailscale running
    checks.append(_check(
        host, "tailscale",
        "tailscale status --self --json 2>/dev/null "
        '| python3 -c "import sys,json; d=json.load(sys.stdin); '
        "print('Online' if d.get('Online') or d.get('Self',{}).get('Online') else 'Offline')\" "
        "2>/dev/null || tailscale status --self 2>/dev/null | head -1",
        validate=lambda out: "online" in out.lower(),
        hint="Start Tailscale: sudo tailscale up",
    ))

    # 6-7. Per-service directory checks
    for compose_dir in effective_dirs:
        dir_label = compose_dir.rstrip("/").rsplit("/", 1)[-1]

        checks.append(_check(
            host, f"compose_dir:{dir_label}",
            f"test -f {compose_dir}/docker-compose.yml && echo exists",
            validate=lambda out: "exists" in out,
            hint=f"Create {compose_dir}/ with docker-compose.yml",
        ))

        checks.append(_check(
            host, f"env_file:{dir_label}",
            f"test -f {compose_dir}/.env && echo exists",
            validate=lambda out: "exists" in out,
            hint=f"Create {compose_dir}/.env from .env.example",
        ))

    all_ok = all(c["status"] == "ok" for c in checks)

    return {
        "host": host,
        "compose_dirs": effective_dirs,
        "all_ok": all_ok,
        "checks": {c["check"]: c["status"] for c in checks},
        "details": checks,
    }
