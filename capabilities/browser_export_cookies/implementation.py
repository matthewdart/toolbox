"""Core capability: export browser cookies for a domain to a Netscape cookies.txt file."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class CookieExportError(Exception):
    """Base error for cookie export failures."""


class DependencyError(CookieExportError):
    """Raised when yt-dlp is not available."""


class ExtractionError(CookieExportError):
    """Raised when browser cookie extraction fails."""


class _Logger:
    """Minimal logger matching the interface yt-dlp expects."""

    def __init__(self, *, quiet: bool) -> None:
        self._quiet = quiet

    def debug(self, msg: str) -> None:
        if not self._quiet:
            print(msg, file=sys.stderr)

    def info(self, msg: str) -> None:
        if not self._quiet:
            print(msg, file=sys.stderr)

    def warning(self, msg: str) -> None:
        print(msg, file=sys.stderr)

    def error(self, msg: str) -> None:
        print(msg, file=sys.stderr)


def _matches_domain(cookie_domain: str, target_domain: str, *, include_subdomains: bool) -> bool:
    cd = (cookie_domain or "").lstrip(".").lower()
    td = (target_domain or "").lstrip(".").lower()
    if not cd or not td:
        return False
    if include_subdomains:
        return cd == td or cd.endswith("." + td)
    return cd == td


def _filter_cookies(jar: Iterable[object], *, domain: str, include_subdomains: bool) -> List[object]:
    out: List[object] = []
    for cookie in jar:
        cookie_domain = getattr(cookie, "domain", None)
        if isinstance(cookie_domain, str) and _matches_domain(
            cookie_domain, domain, include_subdomains=include_subdomains
        ):
            out.append(cookie)
    return out


def export_cookies(
    domain: str,
    output: str,
    browser: str = "safari",
    profile: Optional[str] = None,
    container: Optional[str] = None,
    keyring: Optional[str] = None,
    include_subdomains: bool = True,
    quiet: bool = False,
) -> Dict[str, Any]:
    """Export browser cookies for a domain to a Netscape cookies.txt file.

    Returns a dict with the output path and cookie count.
    """
    try:
        from yt_dlp.cookies import YoutubeDLCookieJar, extract_cookies_from_browser
    except Exception as exc:
        raise DependencyError("yt-dlp is required: pip install yt-dlp") from exc

    out_path = Path(output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    logger = _Logger(quiet=quiet)

    try:
        jar = extract_cookies_from_browser(
            browser,
            profile,
            logger,
            keyring=keyring,
            container=container,
        )
    except Exception as exc:
        raise ExtractionError(
            f"Failed to extract cookies from browser={browser!r}: {exc}. "
            "This must run on the same machine as the browser profile."
        ) from exc

    filtered = _filter_cookies(jar, domain=domain, include_subdomains=include_subdomains)

    out_jar = YoutubeDLCookieJar(str(out_path))
    for cookie in filtered:
        out_jar.set_cookie(cookie)  # type: ignore[arg-type]

    out_jar.save(ignore_discard=True, ignore_expires=True)

    return {
        "output_path": str(out_path),
        "cookie_count": len(filtered),
    }
