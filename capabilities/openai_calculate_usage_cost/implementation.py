"""Capability: calculate cost/usage summary from an OpenAI usage JSONL log.

This is intentionally separate from any producer (e.g., media.analyze_video) so it can be reused.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class UsageCostError(RuntimeError):
    pass


@dataclass(frozen=True)
class TokenTotals:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class AudioTotals:
    calls: int = 0
    audio_seconds: float = 0.0


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise UsageCostError(f"invalid JSON on line {line_no}: {exc}") from exc
    return events


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except Exception:
        return None


def _sum_tokens_by_model(events: Iterable[Dict[str, Any]]) -> Dict[str, TokenTotals]:
    out: Dict[str, TokenTotals] = {}
    for ev in events:
        if ev.get("type") != "openai_call":
            continue
        if ev.get("status") != "ok":
            continue
        if ev.get("kind") != "vision_slide":
            continue
        model = str(ev.get("model") or "").strip()
        usage = ev.get("usage") or {}
        inp = _as_int(usage.get("input_tokens")) or 0
        outp = _as_int(usage.get("output_tokens")) or 0
        tot = _as_int(usage.get("total_tokens")) or (inp + outp)
        prev = out.get(model, TokenTotals())
        out[model] = TokenTotals(
            calls=prev.calls + 1,
            input_tokens=prev.input_tokens + inp,
            output_tokens=prev.output_tokens + outp,
            total_tokens=prev.total_tokens + tot,
        )
    return out


def _sum_audio_by_model(events: Iterable[Dict[str, Any]]) -> Dict[str, AudioTotals]:
    out: Dict[str, AudioTotals] = {}
    for ev in events:
        if ev.get("type") != "openai_call":
            continue
        if ev.get("status") != "ok":
            continue
        if ev.get("kind") != "audio_transcription":
            continue
        model = str(ev.get("model") or "").strip()
        meta = ev.get("meta") or {}
        secs = _as_float(meta.get("audio_seconds")) or 0.0
        prev = out.get(model, AudioTotals())
        out[model] = AudioTotals(calls=prev.calls + 1, audio_seconds=prev.audio_seconds + secs)
    return out


def _calc_token_cost(
    totals: TokenTotals,
    price_in_per_1m: float,
    price_out_per_1m: float,
) -> float:
    return (totals.input_tokens / 1_000_000.0) * price_in_per_1m + (totals.output_tokens / 1_000_000.0) * price_out_per_1m


def _calc_audio_cost(audio_seconds: float, price_per_minute: float) -> float:
    return (audio_seconds / 60.0) * price_per_minute


def calculate_usage_cost(
    usage_log_path: str,
    pricing: Dict[str, Any] | None = None,
    *,
    fail_on_unknown_model: bool = True,
) -> Dict[str, Any]:
    """Summarize usage and (optionally) compute estimated cost from a JSONL log.

    Pricing is intentionally user-supplied because model prices change over time.
    """
    path = Path(usage_log_path).expanduser().resolve()
    if not path.is_file():
        raise UsageCostError(f"usage log not found: {path}")

    events = _read_jsonl(path)
    token_by_model = _sum_tokens_by_model(events)
    audio_by_model = _sum_audio_by_model(events)

    currency = "USD"
    token_prices: Dict[str, Any] = {}
    audio_prices: Dict[str, Any] = {}
    if pricing:
        currency = str(pricing.get("currency") or currency)
        token_prices = pricing.get("token_models") or {}
        audio_prices = pricing.get("audio_models") or {}

    unknown_models: List[str] = []
    line_items: List[Dict[str, Any]] = []

    total_cost: float | None = 0.0 if pricing else None

    # Token models
    for model, totals in sorted(token_by_model.items(), key=lambda kv: kv[0]):
        item: Dict[str, Any] = {
            "model": model,
            "kind": "tokens",
            "calls": totals.calls,
            "input_tokens": totals.input_tokens,
            "output_tokens": totals.output_tokens,
            "total_tokens": totals.total_tokens,
            "audio_seconds": 0.0,
            "audio_minutes": 0.0,
            "unit_prices": None,
            "cost": None,
        }
        if pricing:
            price = token_prices.get(model)
            if not price:
                unknown_models.append(model)
                if fail_on_unknown_model:
                    raise UsageCostError(f"missing token pricing for model: {model}")
            else:
                price_in = float(price.get("input_per_1m"))
                price_out = float(price.get("output_per_1m"))
                item["unit_prices"] = {"input_per_1m": price_in, "output_per_1m": price_out}
                item["cost"] = _calc_token_cost(totals, price_in_per_1m=price_in, price_out_per_1m=price_out)
                total_cost = (total_cost or 0.0) + float(item["cost"])
        line_items.append(item)

    # Audio models
    for model, totals in sorted(audio_by_model.items(), key=lambda kv: kv[0]):
        minutes = totals.audio_seconds / 60.0
        item = {
            "model": model,
            "kind": "audio_minutes",
            "calls": totals.calls,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "audio_seconds": totals.audio_seconds,
            "audio_minutes": minutes,
            "unit_prices": None,
            "cost": None,
        }
        if pricing:
            price = audio_prices.get(model)
            if not price:
                unknown_models.append(model)
                if fail_on_unknown_model:
                    raise UsageCostError(f"missing audio pricing for model: {model}")
            else:
                per_min = float(price.get("per_minute"))
                item["unit_prices"] = {"per_minute": per_min}
                item["cost"] = _calc_audio_cost(totals.audio_seconds, price_per_minute=per_min)
                total_cost = (total_cost or 0.0) + float(item["cost"])
        line_items.append(item)

    total_input = sum(t.input_tokens for t in token_by_model.values())
    total_output = sum(t.output_tokens for t in token_by_model.values())
    total_tokens = sum(t.total_tokens for t in token_by_model.values())
    total_audio_seconds = sum(a.audio_seconds for a in audio_by_model.values())

    summary = {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "total_audio_seconds": total_audio_seconds,
        "total_audio_minutes": total_audio_seconds / 60.0,
    }

    return {
        "currency": currency,
        "total_cost": total_cost,
        "summary": summary,
        "line_items": line_items,
        "unknown_models": sorted(set(unknown_models)),
    }

