#!/usr/bin/env python3
"""Deploy Docker Compose services on a remote host via SSH."""

import argparse
import json
import shutil
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy Docker Compose services on a remote host via SSH.",
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
        help="Specific services to deploy (default: all)",
    )
    parser.add_argument(
        "--pull-only",
        action="store_true",
        help="Pull images without restarting services",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the SSH command without executing",
    )
    return parser.parse_args()


def build_remote_command(compose_dir: str, services: list[str], pull_only: bool) -> str:
    svc_args = " ".join(services)
    pull_cmd = f"docker compose pull {svc_args}".strip()
    if pull_only:
        return f"cd {compose_dir} && {pull_cmd}"
    up_cmd = f"docker compose up -d {svc_args}".strip()
    return f"cd {compose_dir} && {pull_cmd} && {up_cmd}"


def run_ssh(host: str, remote_cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def main() -> int:
    args = parse_args()

    if not shutil.which("ssh"):
        raise SystemExit("ssh not found in PATH")

    remote_cmd = build_remote_command(args.compose_dir, args.services, args.pull_only)
    ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", args.host, remote_cmd]

    if args.dry_run:
        result = {
            "host": args.host,
            "compose_dir": args.compose_dir,
            "services": args.services or ["(all)"],
            "action": "dry_run",
            "ssh_command": ssh_cmd,
        }
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    proc = run_ssh(args.host, remote_cmd)

    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)

    action = "pulled" if args.pull_only else "deployed"
    result = {
        "host": args.host,
        "compose_dir": args.compose_dir,
        "services": args.services or ["(all)"],
        "action": action,
        "exit_code": proc.returncode,
    }

    if proc.returncode != 0:
        result["error"] = proc.stderr.strip() or "remote command failed"

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
