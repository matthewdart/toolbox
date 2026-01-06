#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys


def fetch_html(url: str) -> str:
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl not found in PATH")

    result = subprocess.run(
        [curl, "-fsSL", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "curl failed"
        raise RuntimeError(message)
    return result.stdout


def extract_markdown(html: str) -> str:
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
        try:
            idx = data.index("content")
        except ValueError:
            continue
        if idx + 1 < len(data):
            return data[idx + 1]
    raise RuntimeError("markdown content not found in canvas payload")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract markdown from a ChatGPT canvas shared URL."
    )
    parser.add_argument("url", nargs="?", help="Canvas share URL")
    parser.add_argument("-o", "--output", help="Write markdown to file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = args.url or sys.stdin.read().strip()
    if not url:
        raise SystemExit("missing URL (provide as arg or stdin)")

    html = fetch_html(url)
    markdown = extract_markdown(html)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(markdown)
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
