#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from typing import Optional, Tuple


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


DEFAULT_BASENAME = "canvas"


def extract_payload(html: str) -> Tuple[Optional[str], str]:
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
        title = None
        try:
            title_idx = data.index("title")
        except ValueError:
            title_idx = None
        if title_idx is not None and title_idx + 1 < len(data):
            title = data[title_idx + 1]
        try:
            content_idx = data.index("content")
        except ValueError:
            continue
        if content_idx + 1 < len(data):
            return title, data[content_idx + 1]
    raise RuntimeError("markdown content not found in canvas payload")


def slugify_title(title: Optional[str]) -> str:
    if not title:
        return DEFAULT_BASENAME
    normalized = unicodedata.normalize("NFKD", title)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text or DEFAULT_BASENAME


def suggest_filename(title: Optional[str]) -> str:
    return f"{slugify_title(title)}.md"


def resolve_output_path(output_arg: str, title: Optional[str]) -> str:
    if output_arg == "auto":
        return suggest_filename(title)
    if output_arg.endswith(os.sep) and not os.path.isdir(output_arg):
        raise RuntimeError(f"output directory not found: {output_arg}")
    if os.path.isdir(output_arg):
        return os.path.join(output_arg, suggest_filename(title))
    return output_arg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract markdown from a ChatGPT canvas shared URL."
    )
    parser.add_argument("url", nargs="?", help="Canvas share URL")
    parser.add_argument("-o", "--output", help="Write markdown to file")
    parser.add_argument(
        "--print-filename",
        action="store_true",
        help="Print the suggested filename or output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = args.url or sys.stdin.read().strip()
    if not url:
        raise SystemExit("missing URL (provide as arg or stdin)")

    html = fetch_html(url)
    title, markdown = extract_payload(html)

    if args.output:
        output_path = resolve_output_path(args.output, title)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(markdown)
        if args.print_filename:
            sys.stdout.write(output_path)
    elif args.print_filename:
        sys.stdout.write(suggest_filename(title))
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
