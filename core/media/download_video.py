"""Download a video from a URL using yt-dlp.

Prototype-mode implementation intended for internal tooling. Supports many platforms via yt-dlp
and can use a cookies.txt for authenticated sessions.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class VideoDownloadError(RuntimeError):
    pass


_URL_RE = re.compile(r"https?://[^\s\"'>]+")
_MEDIA_URL_RE = re.compile(r"https?://[^\s\"'>]+\.(?:m3u8|mp4)(?:\?[^\s\"'>]+)?", re.IGNORECASE)
_ESCAPED_SLASH_RE = re.compile(r"\\+/")


def _ffmpeg_location() -> str | None:
    env = os.environ.get("FFMPEG_BIN") or os.environ.get("FFMPEG_PATH")
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return str(p)

    in_path = shutil.which("ffmpeg")
    if in_path:
        return in_path

    try:
        import imageio_ffmpeg  # type: ignore
    except Exception:
        imageio_ffmpeg = None  # type: ignore

    if imageio_ffmpeg is None:
        return None
    try:
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None
    return exe if exe and Path(exe).exists() else None


def _coerce_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _coerce_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_coerce_jsonable(v) for v in value]
    return str(value)


def _iter_entries(info: Any) -> List[Dict[str, Any]]:
    if not isinstance(info, dict):
        return []
    entries = info.get("entries")
    if entries is None:
        return [info]
    if not isinstance(entries, list):
        try:
            entries = list(entries)
        except Exception:
            entries = []
    return [e for e in entries if isinstance(e, dict)]


def _maybe_number(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _entry_filesize(entry: Dict[str, Any]) -> float | None:
    return _maybe_number(entry.get("filesize")) or _maybe_number(entry.get("filesize_approx"))


def _entry_path(entry: Dict[str, Any]) -> str | None:
    # Prefer explicit requested_downloads filepaths (populated after download on many sites).
    req = entry.get("requested_downloads")
    if isinstance(req, list) and req:
        for item in req:
            if isinstance(item, dict):
                fp = item.get("filepath") or item.get("filename")
                if isinstance(fp, str) and fp.strip():
                    return fp

    for key in ("filepath", "_filename"):
        fp = entry.get(key)
        if isinstance(fp, str) and fp.strip():
            return fp
    return None


def _is_brighttalk_url(url: str) -> bool:
    return "brighttalk.com" in (url or "").lower()


def _brighttalk_webcast_id(url: str) -> str | None:
    # Expected patterns:
    # - https://www.brighttalk.com/webcast/<channelId>/<webcastId>
    # - https://www.brighttalk.com/webcast/player/<webcastId>
    m = re.search(r"/webcast/player/(?P<id>\\d+)(?:/|$|\\?)", url)
    if m:
        return m.group("id")
    m = re.search(r"/webcast/\\d+/(?P<id>\\d+)(?:/|$|\\?)", url)
    if m:
        return m.group("id")
    return None


def _curl_fetch_text(
    url: str,
    *,
    cookies_path: Path | None,
    user_agent: str | None,
    referer: str | None,
    headers: Dict[str, str] | None,
) -> str:
    curl = shutil.which("curl")
    if not curl:
        raise VideoDownloadError("curl is required for BrightTALK fallback fetching (curl not found in PATH)")

    cmd = [curl, "-fsSL", "-A", user_agent or "Mozilla/5.0"]
    if referer:
        cmd += ["-e", referer]
    if cookies_path is not None:
        cmd += ["-b", str(cookies_path)]
    if headers:
        for k, v in headers.items():
            if k.lower() in {"user-agent", "referer", "cookie"}:
                continue
            cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise VideoDownloadError(f"failed to fetch page HTML (curl): {proc.stderr.strip()}")
    return proc.stdout


def _cookies_header_from_netscape(cookies_path: Path, *, domain_suffix: str) -> str | None:
    # Netscape cookie format:
    # domain \t flag \t path \t secure \t expiration \t name \t value
    pairs: Dict[str, str] = {}
    for line in cookies_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _, _, _, _, name, value = parts[:7]
        domain = domain.lstrip(".")
        if not domain.endswith(domain_suffix):
            continue
        pairs[str(name)] = str(value)
    if not pairs:
        return None
    return "; ".join(f"{k}={v}" for k, v in pairs.items())


def _extract_media_urls_from_html(html: str) -> List[str]:
    # BrightTALK often embeds URLs inside JSON with escaped slashes and unicode escapes.
    normalized = (
        html.replace("\\u0026", "&")
        .replace("\\u003d", "=")
        .replace("\\u002F", "/")
    )
    normalized = _ESCAPED_SLASH_RE.sub("/", normalized)

    urls = set(_MEDIA_URL_RE.findall(normalized))
    # Some URLs may appear without scheme (//cdn...) - add https:
    for m in re.findall(r"//[^\s\"'>]+\.(?:m3u8|mp4)(?:\?[^\s\"'>]+)?", normalized, flags=re.IGNORECASE):
        urls.add("https:" + m)

    return sorted(urls)


def _pick_best_media_url(urls: List[str]) -> str | None:
    if not urls:
        return None

    def score(u: str) -> tuple[int, int]:
        u_low = u.lower()
        is_mp4 = 1 if u_low.endswith(".mp4") or ".mp4?" in u_low else 0
        # Prefer higher resolution hints when present.
        res = 0
        for key, val in [("2160", 2160), ("1440", 1440), ("1080", 1080), ("720", 720), ("480", 480), ("360", 360)]:
            if key in u_low:
                res = val
                break
        return (is_mp4, res)

    return max(urls, key=score)


def _curl_download_file(
    url: str,
    dst: Path,
    *,
    cookies_path: Path | None,
    user_agent: str | None,
    referer: str | None,
    headers: Dict[str, str] | None,
    overwrite: bool,
) -> None:
    curl = shutil.which("curl")
    if not curl:
        raise VideoDownloadError("curl is required for direct downloads (curl not found in PATH)")

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not overwrite:
        return

    cmd = [curl, "-fL", "-A", user_agent or "Mozilla/5.0"]
    if referer:
        cmd += ["-e", referer]
    if cookies_path is not None:
        cmd += ["-b", str(cookies_path)]
    if headers:
        for k, v in headers.items():
            if k.lower() in {"user-agent", "referer", "cookie"}:
                continue
            cmd += ["-H", f"{k}: {v}"]
    cmd += ["-o", str(dst), url]

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise VideoDownloadError(f"download failed (curl): {proc.stderr.strip()}")


def _ffmpeg_download_hls(
    m3u8_url: str,
    dst: Path,
    *,
    cookies_path: Path | None,
    user_agent: str | None,
    referer: str | None,
    headers: Dict[str, str] | None,
    overwrite: bool,
) -> None:
    ffmpeg = _ffmpeg_location()
    if not ffmpeg:
        raise VideoDownloadError("ffmpeg not found (required for HLS downloads). Install ffmpeg or imageio-ffmpeg.")

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not overwrite:
        return

    header_lines: List[str] = []
    if referer:
        header_lines.append(f"Referer: {referer}")
    if headers:
        for k, v in headers.items():
            if k.lower() in {"user-agent", "referer"}:
                continue
            if k.lower() == "cookie":
                header_lines.append(f"Cookie: {v}")
            else:
                header_lines.append(f"{k}: {v}")
    if cookies_path is not None and not any(h.lower().startswith("cookie:") for h in header_lines):
        cookie_header = _cookies_header_from_netscape(cookies_path, domain_suffix="brighttalk.com")
        if cookie_header:
            header_lines.append(f"Cookie: {cookie_header}")

    header_arg = ""
    if header_lines:
        header_arg = "".join(h + "\\r\\n" for h in header_lines)

    cmd = [ffmpeg, "-y" if overwrite else "-n"]
    if user_agent:
        cmd += ["-user_agent", user_agent]
    if header_arg:
        cmd += ["-headers", header_arg]
    cmd += [
        "-i",
        m3u8_url,
        "-c",
        "copy",
        "-bsf:a",
        "aac_adtstoasc",
        str(dst),
    ]

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise VideoDownloadError(f"ffmpeg HLS download failed: {proc.stderr.strip()}")


def _download_brighttalk(
    url: str,
    *,
    out_root: Path,
    cookies_path: Path | None,
    user_agent: str | None,
    referer: str | None,
    headers: Dict[str, str] | None,
    download: bool,
    overwrite: bool,
    quiet: bool,
    write_info_json: bool,
) -> Dict[str, Any]:
    webcast_id = _brighttalk_webcast_id(url)
    candidate_pages = [url]
    if webcast_id:
        candidate_pages.append(f"https://www.brighttalk.com/webcast/player/{webcast_id}")

    found_urls: List[str] = []
    page_html_by_url: Dict[str, str] = {}
    for page_url in candidate_pages:
        try:
            html = _curl_fetch_text(
                page_url,
                cookies_path=cookies_path,
                user_agent=user_agent,
                referer=referer,
                headers=headers,
            )
        except Exception:
            continue
        page_html_by_url[page_url] = html
        found_urls.extend(_extract_media_urls_from_html(html))

    found_urls = sorted(set(found_urls))
    media_url = _pick_best_media_url(found_urls)
    if not media_url:
        hint = ""
        if cookies_path is None:
            hint = " Try again with cookies_path (BrightTALK playback often requires an authenticated session)."
        raise VideoDownloadError(f"no direct media URL found in BrightTALK pages.{hint}")

    out_name = f"brighttalk_{webcast_id or 'download'}.mp4"
    dst = out_root / out_name

    downloaded = False
    if download:
        if media_url.lower().endswith(".mp4") or ".mp4?" in media_url.lower():
            _curl_download_file(
                media_url,
                dst,
                cookies_path=cookies_path,
                user_agent=user_agent,
                referer=referer,
                headers=headers,
                overwrite=overwrite,
            )
        else:
            _ffmpeg_download_hls(
                media_url,
                dst,
                cookies_path=cookies_path,
                user_agent=user_agent,
                referer=referer,
                headers=headers,
                overwrite=overwrite,
            )
        downloaded = dst.exists()

    info_json_path: Path | None = None
    if write_info_json:
        info_json_path = out_root / "info.json"
        info_json_path.write_text(
            json.dumps(
                {
                    "requested_url": url,
                    "candidate_pages": candidate_pages,
                    "media_url": media_url,
                    "found_media_urls": found_urls,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    return {
        "output_dir": str(out_root),
        "requested_url": str(url),
        "info_json": str(info_json_path) if info_json_path is not None else None,
        "files": [
            {
                "id": webcast_id,
                "title": None,
                "webpage_url": url,
                "extractor": "brighttalk_fallback",
                "duration_seconds": None,
                "ext": "mp4",
                "filesize_bytes": float(dst.stat().st_size) if dst.exists() else None,
                "path": str(dst),
                "downloaded": bool(downloaded),
            }
        ],
    }


def download_video(
    url: str,
    output_dir: str | None = None,
    *,
    filename_template: str | None = None,
    format: str = "bestvideo+bestaudio/best",
    cookies_path: str | None = None,
    headers: Dict[str, str] | None = None,
    user_agent: str | None = None,
    referer: str | None = None,
    allow_playlist: bool = False,
    download: bool = True,
    overwrite: bool = False,
    quiet: bool = False,
    write_info_json: bool = True,
) -> Dict[str, Any]:
    """Download a video URL to a local file and return resolved paths.

    Notes:
    - Only download content you are authorized to download and that complies with the site's terms.
    - For login-gated sites, pass a Netscape-format cookies.txt via cookies_path.
    """
    try:
        from yt_dlp import YoutubeDL  # type: ignore
        from yt_dlp.utils import DownloadError  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise VideoDownloadError("yt-dlp is required. Install it with: pip install yt-dlp") from exc

    if not url or not str(url).strip():
        raise VideoDownloadError("url is required")

    out_root = Path(output_dir).expanduser().resolve() if output_dir else (Path.cwd() / "downloads")
    out_root.mkdir(parents=True, exist_ok=True)

    cookie_path: Path | None = None
    if cookies_path:
        cookie_path = Path(cookies_path).expanduser().resolve()
        if not cookie_path.is_file():
            raise VideoDownloadError(f"cookies_path not found: {cookie_path}")

    http_headers: Dict[str, str] = {}
    if headers:
        http_headers.update({str(k): str(v) for k, v in headers.items()})
    if user_agent:
        http_headers["User-Agent"] = str(user_agent)
    if referer:
        http_headers["Referer"] = str(referer)

    ffmpeg = _ffmpeg_location()

    ydl_opts: Dict[str, Any] = {
        "format": format,
        "paths": {"home": str(out_root)},
        "outtmpl": filename_template or "%(title)s [%(id)s].%(ext)s",
        "noplaylist": not bool(allow_playlist),
        "overwrites": bool(overwrite),
        "quiet": bool(quiet),
        "no_warnings": bool(quiet),
        "retries": 3,
        "fragment_retries": 3,
        "continuedl": True,
        "concurrent_fragment_downloads": 3,
        "merge_output_format": "mp4",
    }

    if cookie_path is not None:
        ydl_opts["cookiefile"] = str(cookie_path)
    if http_headers:
        ydl_opts["http_headers"] = http_headers
    if ffmpeg:
        ydl_opts["ffmpeg_location"] = ffmpeg

    downloaded_paths: List[str] = []

    def _hook(d: Dict[str, Any]) -> None:
        # "finished" is emitted before post-processing, but is still useful as a hint.
        if d.get("status") == "finished":
            fp = d.get("filename") or d.get("filepath")
            if isinstance(fp, str) and fp.strip() and fp not in downloaded_paths:
                downloaded_paths.append(fp)

    ydl_opts["progress_hooks"] = [_hook]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=bool(download))
    except DownloadError as exc:
        # yt-dlp doesn't support all platforms (e.g., BrightTALK). Try a platform-specific fallback.
        msg = str(exc)
        if "Unsupported URL" in msg and _is_brighttalk_url(url):
            if not quiet:
                # Keep output minimal by default; user can inspect info.json for details.
                pass
            return _download_brighttalk(
                url,
                out_root=out_root,
                cookies_path=cookie_path,
                user_agent=user_agent,
                referer=referer,
                headers=http_headers or None,
                download=bool(download),
                overwrite=bool(overwrite),
                quiet=bool(quiet),
                write_info_json=bool(write_info_json),
            )
        raise VideoDownloadError(msg) from exc

    info_json_path: Path | None = None
    if write_info_json:
        info_json_path = out_root / "info.json"
        info_json_path.write_text(
            json.dumps(_coerce_jsonable(info), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    entries = _iter_entries(info)
    files: List[Dict[str, Any]] = []
    for entry in entries:
        path = _entry_path(entry)
        # Best-effort: if we saw progress hook filenames, prefer an existing one.
        if path is None and downloaded_paths:
            for candidate in reversed(downloaded_paths):
                if Path(candidate).exists():
                    path = candidate
                    break

        files.append(
            {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "webpage_url": entry.get("webpage_url") or entry.get("original_url"),
                "extractor": entry.get("extractor_key") or entry.get("extractor"),
                "duration_seconds": _maybe_number(entry.get("duration")),
                "ext": entry.get("ext"),
                "filesize_bytes": _entry_filesize(entry),
                "path": path,
                "downloaded": bool(download) and bool(path) and Path(path).exists(),
            }
        )

    return {
        "output_dir": str(out_root),
        "requested_url": str(url),
        "info_json": str(info_json_path) if info_json_path is not None else None,
        "files": files,
    }
