"""CLI helper for `media.download_video`.

Example:
  .venv/bin/python scripts/download_video.py "https://example.com/video" -o /tmp/video
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from capabilities.media_download_video.implementation import download_video


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a video from a URL using yt-dlp.")
    parser.add_argument("url", help="Video URL (page URL or direct media URL)")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Output directory (default: ./downloads)",
    )
    parser.add_argument("--format", default="bestvideo+bestaudio/best", help="yt-dlp format selector")
    parser.add_argument("--filename-template", default=None, help="yt-dlp output template")
    parser.add_argument("--cookies-path", default=None, help="Path to browser-exported cookies.txt (Netscape format)")
    parser.add_argument("--user-agent", default=None, help="Optional User-Agent header")
    parser.add_argument("--referer", default=None, help="Optional Referer header")
    parser.add_argument("--allow-playlist", action="store_true", help="Allow downloading playlists/multi-entry pages")
    parser.add_argument("--no-download", action="store_true", help="Only extract metadata (do not download)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--quiet", action="store_true", help="Reduce downloader output")
    parser.add_argument("--no-info-json", action="store_true", help="Do not write info.json metadata file")
    return parser.parse_args()


def main() -> int:
    load_dotenv(dotenv_path=Path(".env"))
    args = _parse_args()

    result = download_video(
        args.url,
        output_dir=args.output_dir,
        filename_template=args.filename_template,
        format=args.format,
        cookies_path=args.cookies_path,
        user_agent=args.user_agent,
        referer=args.referer,
        allow_playlist=args.allow_playlist,
        download=not args.no_download,
        overwrite=args.overwrite,
        quiet=args.quiet,
        write_info_json=not args.no_info_json,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

