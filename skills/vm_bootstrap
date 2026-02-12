#!/usr/bin/env python3
"""Preflight check for VM deployment readiness."""

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify a remote VM has prerequisites for the MCP container stack.",
    )
    parser.add_argument(
        "--host",
        required=True,
        help="SSH hostname (e.g. Tailscale hostname or IP)",
    )
    parser.add_argument(
        "--compose-dir",
        default="/opt/mcp",
        help="Expected compose directory on the remote host (default: /opt/mcp)",
    )
    return parser.parse_args()


def run_ssh(host: str, remote_cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def check(
    host: str,
    name: str,
    remote_cmd: str,
    validate: Any = None,
    hint: str = "",
) -> dict:
    """Run a remote check and return a result dict.

    Args:
        host: SSH hostname.
        name: Human-readable check name.
        remote_cmd: Command to run on the remote host.
        validate: Optional callable(stdout) -> bool for extra validation.
        hint: Remediation hint printed to stderr on failure.
    """
    proc = run_ssh(host, remote_cmd)
    stdout = proc.stdout.strip()

    if proc.returncode != 0:
        if hint:
            print(f"  {name}: FAIL - {hint}", file=sys.stderr)
        return {"check": name, "status": "fail", "detail": proc.stderr.strip() or "command failed"}

    if validate and not validate(stdout):
        if hint:
            print(f"  {name}: FAIL - {hint}", file=sys.stderr)
        return {"check": name, "status": "fail", "detail": stdout}

    return {"check": name, "status": "ok", "detail": stdout}


def main() -> int:
    args = parse_args()

    if not shutil.which("ssh"):
        raise SystemExit("ssh not found in PATH")

    print(f"Checking {args.host} ...", file=sys.stderr)

    checks: list[dict] = []

    # 1. Docker installed
    checks.append(check(
        args.host,
        "docker",
        "docker --version",
        hint="Install Docker: https://docs.docker.com/engine/install/ubuntu/",
    ))

    # 2. Docker Compose plugin
    checks.append(check(
        args.host,
        "compose",
        "docker compose version",
        hint="Install Docker Compose plugin: https://docs.docker.com/compose/install/",
    ))

    # 3. Architecture
    checks.append(check(
        args.host,
        "arch",
        "uname -m",
        validate=lambda out: "aarch64" in out or "arm64" in out,
        hint="Expected ARM64 architecture (aarch64)",
    ))

    # 4. GHCR authentication
    checks.append(check(
        args.host,
        "ghcr",
        'python3 -c "import json; d=json.load(open(\\"/home/ubuntu/.docker/config.json\\")); print(\\"authenticated\\" if \\"ghcr.io\\" in d.get(\\"auths\\",{}) else \\"unauthenticated\\")" 2>/dev/null || echo unauthenticated',
        validate=lambda out: "authenticated" == out.strip() and "un" not in out.strip(),
        hint="Authenticate: echo $GHCR_TOKEN | docker login ghcr.io -u <user> --password-stdin",
    ))

    # 5. Tailscale running
    checks.append(check(
        args.host,
        "tailscale",
        "tailscale status --self --json 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print('Online' if d.get('Online') or d.get('Self',{}).get('Online') else 'Offline')\" 2>/dev/null || tailscale status --self 2>/dev/null | head -1",
        validate=lambda out: "online" in out.lower(),
        hint="Start Tailscale: sudo tailscale up",
    ))

    # 6. Compose directory exists with docker-compose.yml
    checks.append(check(
        args.host,
        "compose_dir",
        f"test -f {args.compose_dir}/docker-compose.yml && echo exists",
        validate=lambda out: "exists" in out,
        hint=f"Create {args.compose_dir}/ with docker-compose.yml",
    ))

    # 7. .env file present
    checks.append(check(
        args.host,
        "env_file",
        f"test -f {args.compose_dir}/.env && echo exists",
        validate=lambda out: "exists" in out,
        hint=f"Create {args.compose_dir}/.env from .env.example",
    ))

    all_ok = all(c["status"] == "ok" for c in checks)

    result = {
        "host": args.host,
        "compose_dir": args.compose_dir,
        "all_ok": all_ok,
        "checks": {c["check"]: c["status"] for c in checks},
        "details": checks,
    }

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
