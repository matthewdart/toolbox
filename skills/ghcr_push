#!/usr/bin/env python3
"""Build a Docker image for a specified platform and push to GHCR."""

import argparse
import json
import shutil
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Docker image and push to GitHub Container Registry.",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Image repository path (e.g. matthewdart/health-ledger)",
    )
    parser.add_argument(
        "--context",
        required=True,
        help="Docker build context path",
    )
    parser.add_argument(
        "--dockerfile",
        default="Dockerfile",
        help="Path to Dockerfile relative to context (default: Dockerfile)",
    )
    parser.add_argument(
        "--platform",
        default="linux/arm64",
        help="Target platform (default: linux/arm64)",
    )
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="Image tag (repeatable; default: latest)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the docker command without executing",
    )
    return parser.parse_args()


def build_docker_cmd(
    repo: str,
    context: str,
    dockerfile: str,
    platform: str,
    tags: list[str],
) -> list[str]:
    image_base = f"ghcr.io/{repo}"
    cmd = [
        "docker", "buildx", "build",
        "--platform", platform,
        "-f", dockerfile,
    ]
    for tag in tags:
        cmd += ["-t", f"{image_base}:{tag}"]
    cmd += ["--push", context]
    return cmd


def main() -> int:
    args = parse_args()

    if not shutil.which("docker"):
        raise SystemExit("docker not found in PATH")

    tags = args.tags or ["latest"]
    image_base = f"ghcr.io/{args.repo}"

    cmd = build_docker_cmd(args.repo, args.context, args.dockerfile, args.platform, tags)

    if args.dry_run:
        result = {
            "image": image_base,
            "tags": tags,
            "platform": args.platform,
            "action": "dry_run",
            "docker_command": cmd,
        }
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)

    if proc.returncode != 0:
        result = {
            "image": image_base,
            "tags": tags,
            "platform": args.platform,
            "action": "failed",
            "exit_code": proc.returncode,
            "error": proc.stderr.strip() or "docker buildx build failed",
        }
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return proc.returncode

    result = {
        "image": image_base,
        "tags": tags,
        "platform": args.platform,
        "action": "pushed",
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
