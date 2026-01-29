"""CLI helper for `media.analyze_video`.

Example:
  .venv/bin/python scripts/analyze_video_openai.py /tmp/video.mp4 -o ./out/video
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

from core.media.analyze_video import analyze_video


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe a video and extract key slides using OpenAI APIs.")
    parser.add_argument("video_path", help="Path to a local video file (e.g., .mp4)")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Output directory (default: ./<video_stem>_analysis)",
    )
    parser.add_argument("--transcribe-model", default="whisper-1")
    parser.add_argument("--vision-model", default="gpt-4.1")
    parser.add_argument("--vision-temperature", type=float, default=0.0)
    parser.add_argument("--chunk-seconds", type=int, default=600)
    parser.add_argument("--scene-threshold", type=float, default=0.30)
    parser.add_argument("--max-frames", type=int, default=80)
    parser.add_argument("--fallback-interval-seconds", type=int, default=10)
    parser.add_argument("--dedupe-window-seconds", type=int, default=180)
    parser.add_argument("--dedupe-min-token-cover", type=float, default=0.95)
    parser.add_argument("--dedupe-min-seq-ratio", type=float, default=0.985)
    parser.add_argument("--max-slides", type=int, default=15)
    parser.add_argument("--slide-confidence-threshold", type=float, default=0.60)
    parser.add_argument("--keep-intermediate", action="store_true")
    parser.add_argument("--log-usage", action="store_true", help="Write per-call OpenAI usage events to JSONL.")
    parser.add_argument(
        "--usage-log-path",
        default=None,
        help="Optional path for usage JSONL (relative paths resolve under output_dir).",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv(dotenv_path=Path(".env"))
    args = _parse_args()
    result = analyze_video(
        args.video_path,
        output_dir=args.output_dir,
        transcribe_model=args.transcribe_model,
        vision_model=args.vision_model,
        vision_temperature=args.vision_temperature,
        chunk_seconds=args.chunk_seconds,
        scene_threshold=args.scene_threshold,
        max_frames=args.max_frames,
        fallback_interval_seconds=args.fallback_interval_seconds,
        dedupe_window_seconds=args.dedupe_window_seconds,
        dedupe_min_token_cover=args.dedupe_min_token_cover,
        dedupe_min_seq_ratio=args.dedupe_min_seq_ratio,
        max_slides=args.max_slides,
        slide_confidence_threshold=args.slide_confidence_threshold,
        keep_intermediate=args.keep_intermediate,
        log_usage=args.log_usage,
        usage_log_path=args.usage_log_path,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
