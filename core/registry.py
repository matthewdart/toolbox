"""Capability registry for core dispatch."""
from __future__ import annotations

from typing import Any, Callable, Dict

from core.bsport.list_offers import list_offers
from core.media.analyze_video import analyze_video
from core.openai.calculate_usage_cost import calculate_usage_cost
from core.text.normalize_markdown import normalize_markdown


REGISTRY: Dict[str, Callable[..., Any]] = {
    "bsport.list_offers": list_offers,
    "media.analyze_video": analyze_video,
    "openai.calculate_usage_cost": calculate_usage_cost,
    "text.normalize_markdown": normalize_markdown,
}
