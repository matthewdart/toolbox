#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

API_BASE = "https://api.production.bsport.io/book/v1/offer/"
DEFAULT_COMPANY = 995
DEFAULT_DAYS = 7
DEFAULT_LIMIT = 50
ORDERING = "-date_start"


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


def build_url(company: int) -> str:
    params = {"company": company, "ordering": ORDERING}
    return f"{API_BASE}?{urlencode(params)}"


def run_curl(url: str) -> str:
    curl = shutil.which("curl")
    if not curl:
        raise SystemExit("curl not found in PATH")

    result = subprocess.run(
        [curl, "-fsSL", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "curl failed"
        raise SystemExit(message)
    return result.stdout


def fetch_json(url: str) -> Dict[str, Any]:
    raw = run_curl(url)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON response: {exc}")


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    effectif = offer.get("effectif")
    validated = offer.get("validated_booking_count")
    spots_left = None
    if isinstance(effectif, int) and isinstance(validated, int):
        spots_left = max(effectif - validated, 0)

    return {
        "id": offer.get("id"),
        "company": offer.get("company"),
        "activity_name": offer.get("activity_name"),
        "date_start": offer.get("date_start"),
        "duration_minute": offer.get("duration_minute"),
        "timezone_name": offer.get("timezone_name"),
        "available": offer.get("available"),
        "full": offer.get("full"),
        "effectif": effectif,
        "validated_booking_count": validated,
        "spots_left": spots_left,
        "establishment": offer.get("establishment"),
        "coach": offer.get("coach"),
        "meta_activity": offer.get("meta_activity"),
    }


def offer_sort_key(offer: Dict[str, Any]) -> datetime:
    parsed = parse_date(offer.get("date_start"))
    if not parsed:
        return datetime.max.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def collect_offers(
    company: int,
    days: int,
    limit: Optional[int],
    activity_filters: List[str],
    coach_filters: List[int],
    available_only: bool,
) -> tuple[List[Dict[str, Any]], datetime, Optional[datetime]]:
    now = datetime.now(timezone.utc)
    end: Optional[datetime]
    if days == 0:
        end = None
    else:
        end = now + timedelta(days=days)

    url = build_url(company)
    offers: List[Dict[str, Any]] = []
    seen_urls = set()

    while url:
        if url in seen_urls:
            raise SystemExit("pagination loop detected")
        seen_urls.add(url)

        payload = fetch_json(url)
        results = payload.get("results") or []
        stop = False

        for offer in results:
            start = parse_date(offer.get("date_start"))
            if not start:
                continue
            start_utc = start.astimezone(timezone.utc)
            if start_utc < now:
                stop = True
                break
            if end and start_utc > end:
                continue
            if available_only and not offer.get("available"):
                continue
            if coach_filters:
                coach = offer.get("coach")
                coach_override = offer.get("coach_override")
                if coach not in coach_filters and coach_override not in coach_filters:
                    continue
            if activity_filters:
                name = offer.get("activity_name") or ""
                name_folded = name.casefold()
                if not any(term.casefold() in name_folded for term in activity_filters):
                    continue
            offers.append(offer)
            if limit is not None and len(offers) >= limit:
                stop = True
                break

        if stop:
            break
        url = (payload.get("links") or {}).get("next")

    return offers, now, end


def main() -> int:
    args = parse_args()
    if args.days < 0:
        raise SystemExit("--days must be >= 0")
    if args.limit < 0:
        raise SystemExit("--limit must be >= 0")

    limit = None if args.limit == 0 else args.limit
    activity_filters = [term.strip() for term in (args.activity or []) if term and term.strip()]
    coach_filters = args.coach or []

    offers, now, end = collect_offers(
        args.company,
        args.days,
        limit,
        activity_filters,
        coach_filters,
        args.available_only,
    )
    offers.sort(key=offer_sort_key)

    if not args.raw:
        offers = [normalize_offer(offer) for offer in offers]

    payload = {
        "company": args.company,
        "range_start": now.isoformat(timespec="seconds"),
        "range_end": end.isoformat(timespec="seconds") if end else None,
        "filters": {
            "activity": activity_filters,
            "coach": coach_filters,
            "available_only": args.available_only,
        },
        "count": len(offers),
        "offers": offers,
    }

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    if not args.pretty:
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
