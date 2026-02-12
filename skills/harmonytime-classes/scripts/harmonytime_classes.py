#!/usr/bin/env python3
import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from capabilities.bsport_list_offers.implementation import (  # noqa: E402
    BsportError,
    DEFAULT_COMPANY,
    DEFAULT_DAYS,
    DEFAULT_LIMIT,
    list_offers,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch upcoming Harmony Time classes from bsport offers."
    )
    parser.add_argument(
        "--company",
        type=int,
        default=DEFAULT_COMPANY,
        help="Company id (default: 995 for Harmony Time).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help="Days ahead to include (0 = no end date).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Maximum offers to return (0 = no limit).",
    )
    parser.add_argument(
        "--activity",
        action="append",
        help="Case-insensitive substring match on activity name (repeatable).",
    )
    parser.add_argument(
        "--coach",
        type=int,
        action="append",
        help="Filter by coach id (repeatable).",
    )
    parser.add_argument(
        "--available-only",
        action="store_true",
        help="Only include offers with available=true.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Return raw offer objects instead of a reduced schema.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = list_offers(
            company=args.company,
            days=args.days,
            limit=args.limit,
            activity=args.activity or [],
            coach=args.coach or [],
            available_only=args.available_only,
            raw=args.raw,
        )
    except BsportError as exc:
        raise SystemExit(str(exc))

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    if not args.pretty:
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
