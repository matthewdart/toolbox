#!/usr/bin/env python3
"""Check Docker Compose service status on a remote host via SSH."""

import argparse
import json
import shutil
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Docker Compose service status on a remote host via SSH.",
    )
    parser.add_argument(
        "--host",
        required=True,
        help="SSH hostname (e.g. Tailscale hostname or IP)",
    )
    parser.add_argument(
        "--compose-dir",
        required=True,
        help="Absolute path to the docker-compose.yml directory on the remote host",
    )
    parser.add_argument(
        "--services",
        nargs="*",
        default=[],
        help="Specific services to check (default: all)",
    )
    return parser.parse_args()


def run_ssh(host: str, remote_cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def parse_compose_ps(raw_output: str) -> list[dict]:
    """Parse docker compose ps --format json output.

    Docker Compose may emit one JSON object per line (not a JSON array),
    so handle both formats.
    """
    services: list[dict] = []
    if not raw_output.strip():
        return services

    # Try parsing as a JSON array first
    try:
        data = json.loads(raw_output)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    # Fall back to one-JSON-object-per-line
    for line in raw_output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            services.append(obj)
        except json.JSONDecodeError:
            continue

    return services


def normalize_service(svc: dict) -> dict:
    """Normalize docker compose ps JSON to a consistent schema."""
    return {
        "name": svc.get("Name") or svc.get("Service") or svc.get("name", "unknown"),
        "service": svc.get("Service") or svc.get("service", ""),
        "status": svc.get("State") or svc.get("Status") or svc.get("status", "unknown"),
        "health": svc.get("Health") or svc.get("health", ""),
        "ports": svc.get("Publishers") or svc.get("Ports") or svc.get("ports", ""),
        "image": svc.get("Image") or svc.get("image", ""),
    }


def main() -> int:
    args = parse_args()

    if not shutil.which("ssh"):
        raise SystemExit("ssh not found in PATH")

    svc_args = " ".join(args.services)
    remote_cmd = f"cd {args.compose_dir} && docker compose ps --format json {svc_args}".strip()

    proc = run_ssh(args.host, remote_cmd)

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() or "remote command failed"
        result = {
            "host": args.host,
            "compose_dir": args.compose_dir,
            "error": error_msg,
            "exit_code": proc.returncode,
        }
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return proc.returncode

    raw_services = parse_compose_ps(proc.stdout)
    normalized = [normalize_service(s) for s in raw_services]

    result = {
        "host": args.host,
        "compose_dir": args.compose_dir,
        "service_count": len(normalized),
        "services": normalized,
    }

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
