"""Core capability: fetch upcoming bsport offers with filters."""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

API_BASE = "https://api.production.bsport.io/book/v1/offer/"
DEFAULT_COMPANY = 995
DEFAULT_DAYS = 7
DEFAULT_LIMIT = 50
ORDERING = "-date_start"


class BsportError(Exception):
    """Base error for bsport capability failures."""


class DependencyError(BsportError):
    """Raised when required external dependencies are missing."""


class NetworkError(BsportError):
    """Raised for network or HTTP failures."""


class InvalidResponseError(BsportError):
    """Raised when the API response cannot be parsed as JSON."""


class PaginationLoopError(BsportError):
    """Raised when pagination appears to loop."""


class ValidationError(BsportError):
    """Raised when inputs are invalid."""


def build_url(company: int) -> str:
    params = {"company": company, "ordering": ORDERING}
    return f"{API_BASE}?{urlencode(params)}"


def run_curl(url: str) -> str:
    curl = shutil.which("curl")
    if not curl:
        raise DependencyError("curl not found in PATH")

    result = subprocess.run(
        [curl, "-fsSL", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "curl failed"
        raise NetworkError(message)
    return result.stdout


def fetch_json(url: str) -> Dict[str, Any]:
    raw = run_curl(url)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidResponseError(f"invalid JSON response: {exc}")


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


def coerce_now(now: Optional[datetime]) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def collect_offers(
    company: int,
    days: int,
    limit: Optional[int],
    activity_filters: List[str],
    coach_filters: List[int],
    available_only: bool,
    now: Optional[datetime] = None,
) -> Tuple[List[Dict[str, Any]], datetime, Optional[datetime]]:
    now_utc = coerce_now(now)
    end: Optional[datetime]
    if days == 0:
        end = None
    else:
        end = now_utc + timedelta(days=days)

    url = build_url(company)
    offers: List[Dict[str, Any]] = []
    seen_urls = set()

    while url:
        if url in seen_urls:
            raise PaginationLoopError("pagination loop detected")
        seen_urls.add(url)

        payload = fetch_json(url)
        results = payload.get("results") or []
        stop = False

        for offer in results:
            start = parse_date(offer.get("date_start"))
            if not start:
                continue
            start_utc = start.astimezone(timezone.utc)
            if start_utc < now_utc:
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

    return offers, now_utc, end


def list_offers(
    *,
    company: int = DEFAULT_COMPANY,
    days: int = DEFAULT_DAYS,
    limit: int = DEFAULT_LIMIT,
    activity: Optional[List[str]] = None,
    coach: Optional[List[int]] = None,
    available_only: bool = False,
    raw: bool = False,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Return upcoming offers and summary metadata."""
    if not isinstance(company, int) or company <= 0:
        raise ValidationError("company must be a positive integer")
    if not isinstance(days, int) or days < 0:
        raise ValidationError("days must be >= 0")
    if not isinstance(limit, int) or limit < 0:
        raise ValidationError("limit must be >= 0")

    limit_value = None if limit == 0 else limit
    activity_filters = [
        term.strip() for term in (activity or []) if term and str(term).strip()
    ]
    coach_filters = list(coach or [])

    offers, now_utc, end = collect_offers(
        company,
        days,
        limit_value,
        activity_filters,
        coach_filters,
        available_only,
        now=now,
    )
    offers.sort(key=offer_sort_key)

    if not raw:
        offers = [normalize_offer(offer) for offer in offers]

    payload: Dict[str, Any] = {
        "company": company,
        "range_start": now_utc.isoformat(timespec="seconds"),
        "range_end": end.isoformat(timespec="seconds") if end else None,
        "filters": {
            "activity": activity_filters,
            "coach": coach_filters,
            "available_only": available_only,
        },
        "count": len(offers),
        "offers": offers,
    }
    return payload
