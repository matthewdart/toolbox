#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a private GitHub Gist from files or stdin."
    )
    parser.add_argument("files", nargs="*", help="Files to include; omit to read stdin.")
    parser.add_argument("-d", "--desc", help="Gist description")
    parser.add_argument(
        "-f",
        "--filename",
        help="Filename to use when reading from stdin",
    )
    return parser.parse_args()


def run_gh(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def main() -> int:
    args = parse_args()
    if not shutil.which("gh"):
        raise SystemExit("gh not found in PATH")

    if args.filename and args.files:
        raise SystemExit("--filename is only valid when reading from stdin")

    if "-" in args.files:
        raise SystemExit("'-' cannot be combined with file arguments")

    cmd = ["gh", "gist", "create"]
    if args.desc:
        cmd += ["-d", args.desc]

    if args.files:
        cmd += args.files
        result = run_gh(cmd)
    else:
        content = sys.stdin.read()
        if not content:
            raise SystemExit("missing input (provide files or stdin)")
        cmd.append("-")
        if args.filename:
            cmd += ["-f", args.filename]
        result = run_gh(cmd, input_text=content)

    if result.returncode != 0:
        message = result.stderr.strip() or "gh gist create failed"
        raise SystemExit(message)

    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
