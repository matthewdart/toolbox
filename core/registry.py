"""Capability registry for core dispatch."""
from __future__ import annotations

from typing import Any, Callable, Dict

from core.bsport.list_offers import list_offers
from core.text.normalize_markdown import normalize_markdown


REGISTRY: Dict[str, Callable[..., Any]] = {
    "bsport.list_offers": list_offers,
    "text.normalize_markdown": normalize_markdown,
}
