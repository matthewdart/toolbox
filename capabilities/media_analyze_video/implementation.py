"""Transcribe a video and extract key slides using OpenAI APIs.

Prototype-mode implementation:
- Uses a locally available `ffmpeg`, or falls back to `imageio-ffmpeg` for a bundled binary.
- Calls OpenAI's audio transcription API for transcript generation.
- Calls OpenAI's vision-capable models on extracted frames to identify slides.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI
from openai import BadRequestError


_DEFAULT_FFMPEG_URL = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"


class VideoAnalysisError(RuntimeError):
    pass


def _to_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # pydantic
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "json"):
        return json.loads(obj.json())
    raise TypeError(f"unsupported response type: {type(obj)}")


def _cache_dir() -> Path:
    # Respect XDG-style cache dir when available.
    base = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(base) / "toolbox"


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _safe_extract(tar: tarfile.TarFile, dst: Path) -> None:
    dst_resolved = dst.resolve()
    for member in tar.getmembers():
        member_path = (dst / member.name).resolve()
        if not str(member_path).startswith(str(dst_resolved) + os.sep):
            raise VideoAnalysisError(f"unsafe tar member path: {member.name}")
    tar.extractall(dst)


@dataclass(frozen=True)
class FfmpegBins:
    ffmpeg: Path
    ffprobe: Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class UsageLogger:
    path: Path
    _handle: Any

    @classmethod
    def open(cls, path: Path) -> "UsageLogger":
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = path.open("w", encoding="utf-8")
        return cls(path=path, _handle=handle)

    def log(self, event: Dict[str, Any]) -> None:
        self._handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._handle.flush()

    def close(self) -> None:
        try:
            self._handle.close()
        except Exception:
            pass

    def __enter__(self) -> "UsageLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def ensure_ffmpeg() -> FfmpegBins:
    """Return paths to ffmpeg/ffprobe, downloading a static build if needed."""
    env_ffmpeg = os.environ.get("FFMPEG_BIN") or os.environ.get("FFMPEG_PATH")
    env_ffprobe = os.environ.get("FFPROBE_BIN") or os.environ.get("FFPROBE_PATH")
    if env_ffmpeg:
        ffmpeg_path = Path(env_ffmpeg)
        ffprobe_path = Path(env_ffprobe) if env_ffprobe else ffmpeg_path.with_name("ffprobe")
        if not ffmpeg_path.exists():
            raise VideoAnalysisError(f"FFMPEG_BIN not found: {ffmpeg_path}")
        if not ffprobe_path.exists():
            raise VideoAnalysisError(f"FFPROBE_BIN not found: {ffprobe_path}")
        return FfmpegBins(ffmpeg=ffmpeg_path, ffprobe=ffprobe_path)

    path_ffmpeg = _which("ffmpeg")
    path_ffprobe = _which("ffprobe")
    if path_ffmpeg and path_ffprobe:
        return FfmpegBins(ffmpeg=Path(path_ffmpeg), ffprobe=Path(path_ffprobe))

    cache_root = _cache_dir() / "ffmpeg"
    cache_root.mkdir(parents=True, exist_ok=True)

    # If we already extracted a static build, reuse it.
    candidates = sorted(cache_root.glob("ffmpeg-*-amd64-static"))
    for folder in candidates[::-1]:
        ffmpeg_path = folder / "ffmpeg"
        ffprobe_path = folder / "ffprobe"
        if ffmpeg_path.exists() and ffprobe_path.exists():
            return FfmpegBins(ffmpeg=ffmpeg_path, ffprobe=ffprobe_path)

    # Prefer a cross-platform helper when available.
    try:
        import imageio_ffmpeg  # type: ignore
    except Exception:
        imageio_ffmpeg = None  # type: ignore

    if imageio_ffmpeg is not None:
        ffmpeg_path = Path(imageio_ffmpeg.get_ffmpeg_exe())
        if not ffmpeg_path.exists():
            raise VideoAnalysisError(f"imageio-ffmpeg returned missing ffmpeg path: {ffmpeg_path}")

        # ffprobe may not be present; we don't currently require it, but return a best-effort path.
        ffprobe_path = ffmpeg_path.with_name("ffprobe")
        if not ffprobe_path.exists():
            path_ffprobe = _which("ffprobe")
            ffprobe_path = Path(path_ffprobe) if path_ffprobe else ffmpeg_path

        return FfmpegBins(ffmpeg=ffmpeg_path, ffprobe=ffprobe_path)

    # Fallback: download a Linux amd64 static build (only used when ffmpeg isn't installed).
    import platform

    if platform.system().lower() != "linux" or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise VideoAnalysisError(
            "ffmpeg not found in PATH. Install ffmpeg and set FFMPEG_BIN/FFPROBE_BIN, "
            "or install imageio-ffmpeg to enable automatic download."
        )

    archive_path = cache_root / "ffmpeg-release-amd64-static.tar.xz"

    if not archive_path.exists():
        # Keep it simple: use curl if available; fall back to urllib.
        curl = _which("curl")
        if curl:
            subprocess.run(
                [curl, "-fL", "-o", str(archive_path), _DEFAULT_FFMPEG_URL],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        else:
            import urllib.request

            with urllib.request.urlopen(_DEFAULT_FFMPEG_URL) as resp, open(archive_path, "wb") as out:
                shutil.copyfileobj(resp, out)

    # Extract into a versioned directory (determined by archive contents).
    with tarfile.open(archive_path, mode="r:xz") as tar:
        _safe_extract(tar, cache_root)

    # Locate binaries in extracted folder.
    candidates = sorted(cache_root.glob("ffmpeg-*-amd64-static"))
    for folder in candidates[::-1]:
        ffmpeg_path = folder / "ffmpeg"
        ffprobe_path = folder / "ffprobe"
        if ffmpeg_path.exists() and ffprobe_path.exists():
            ffmpeg_path.chmod(ffmpeg_path.stat().st_mode | 0o111)
            ffprobe_path.chmod(ffprobe_path.stat().st_mode | 0o111)
            return FfmpegBins(ffmpeg=ffmpeg_path, ffprobe=ffprobe_path)

    raise VideoAnalysisError("ffmpeg download/extract succeeded, but binaries were not found")


def _format_srt_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, rem = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{rem:03d}"


def _write_srt(segments: List[Dict[str, Any]], path: Path) -> None:
    lines: List[str] = []
    for idx, seg in enumerate(segments, start=1):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        lines.append(str(idx))
        lines.append(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(end)}")
        lines.append(text)
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


_DURATION_RE = re.compile(r"Duration:\s*(?P<h>\d+):(?P<m>\d+):(?P<s>\d+(?:\.\d+)?)")


def _media_duration_seconds(ffmpeg: Path, media_path: Path) -> float | None:
    # Use ffmpeg parsing (works even when ffprobe isn't available).
    proc = subprocess.run(
        [str(ffmpeg), "-i", str(media_path)],
        text=True,
        capture_output=True,
    )
    text = (proc.stderr or "") + "\n" + (proc.stdout or "")
    m = _DURATION_RE.search(text)
    if not m:
        return None
    hours = int(m.group("h"))
    minutes = int(m.group("m"))
    seconds = float(m.group("s"))
    return hours * 3600 + minutes * 60 + seconds


@dataclass(frozen=True)
class AudioChunk:
    index: int
    path: Path
    duration_seconds: float | None
    size_bytes: int


def _extract_audio_chunks(
    ffmpeg: Path,
    video_path: Path,
    out_dir: Path,
    chunk_seconds: int,
) -> List[AudioChunk]:
    audio_dir = out_dir / "audio_chunks"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # mp3 @ 16kHz mono is compact and widely supported by transcription endpoints.
    out_pattern = str(audio_dir / "chunk_%03d.mp3")
    cmd = [
        str(ffmpeg),
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "64k",
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-reset_timestamps",
        "1",
        out_pattern,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise VideoAnalysisError(f"ffmpeg audio extract failed: {proc.stderr.strip()}")
    chunk_paths = sorted(audio_dir.glob("chunk_*.mp3"))
    # ffmpeg can emit a tiny trailing segment (sub-second). Skip it proactively.
    chunk_paths = [p for p in chunk_paths if p.stat().st_size >= 2048]
    if not chunk_paths:
        raise VideoAnalysisError("no audio chunks produced (is the video readable?)")
    chunks: List[AudioChunk] = []
    for p in chunk_paths:
        m = re.search(r"chunk_(\d+)\.mp3$", p.name)
        idx = int(m.group(1)) if m else len(chunks)
        dur = _media_duration_seconds(ffmpeg, p)
        chunks.append(AudioChunk(index=idx, path=p, duration_seconds=dur, size_bytes=p.stat().st_size))
    return chunks


def _transcribe_chunks(
    client: OpenAI,
    chunks: List[AudioChunk],
    model: str,
    chunk_seconds: int,
    usage_logger: UsageLogger | None = None,
) -> Dict[str, Any]:
    all_segments: List[Dict[str, Any]] = []
    texts: List[str] = []

    for chunk in chunks:
        with chunk.path.open("rb") as handle:
            try:
                resp = client.audio.transcriptions.create(
                    model=model,
                    file=handle,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
            except BadRequestError as exc:
                body = getattr(exc, "body", None)
                code = None
                if isinstance(body, dict):
                    code = (body.get("error") or {}).get("code")
                if code == "audio_too_short" or "audio_too_short" in str(exc):
                    if usage_logger is not None:
                        usage_logger.log(
                            {
                                "type": "openai_call",
                                "ts": _utc_now_iso(),
                                "kind": "audio_transcription",
                                "status": "skipped_audio_too_short",
                                "model": model,
                                "usage": None,
                                "meta": {
                                    "chunk_index": chunk.index,
                                    "audio_seconds": chunk.duration_seconds,
                                    "audio_path": str(chunk.path),
                                    "audio_bytes": chunk.size_bytes,
                                },
                            }
                        )
                    continue
                if usage_logger is not None:
                    usage_logger.log(
                        {
                            "type": "openai_call",
                            "ts": _utc_now_iso(),
                            "kind": "audio_transcription",
                            "status": "error",
                            "model": model,
                            "usage": None,
                            "meta": {
                                "chunk_index": chunk.index,
                                "audio_seconds": chunk.duration_seconds,
                                "audio_path": str(chunk.path),
                                "audio_bytes": chunk.size_bytes,
                                "error": str(exc),
                            },
                        }
                    )
                raise
        if usage_logger is not None:
            usage_logger.log(
                {
                    "type": "openai_call",
                    "ts": _utc_now_iso(),
                    "kind": "audio_transcription",
                    "status": "ok",
                    "model": model,
                    "usage": None,
                    "meta": {
                        "chunk_index": chunk.index,
                        "audio_seconds": chunk.duration_seconds,
                        "audio_path": str(chunk.path),
                        "audio_bytes": chunk.size_bytes,
                    },
                }
            )
        data = _to_dict(resp)
        chunk_text = (data.get("text") or "").strip()
        if chunk_text:
            texts.append(chunk_text)

        offset = chunk.index * float(chunk_seconds)
        for seg in data.get("segments") or []:
            seg = dict(seg)
            if "start" in seg:
                seg["start"] = float(seg["start"]) + offset
            if "end" in seg:
                seg["end"] = float(seg["end"]) + offset
            all_segments.append(seg)

    return {
        "text": "\n".join(texts).strip(),
        "segments": all_segments,
    }


_SHOWINFO_PTS_RE = re.compile(r"pts_time:(?P<pts>[0-9]+(?:\.[0-9]+)?)")


def _extract_scene_frames(
    ffmpeg: Path,
    video_path: Path,
    out_dir: Path,
    scene_threshold: float,
) -> List[Dict[str, Any]]:
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for existing in frames_dir.glob("frame_*"):
        try:
            existing.unlink()
        except OSError:
            pass
    out_pattern = str(frames_dir / "frame_%04d.png")

    cmd = [
        str(ffmpeg),
        "-y",
        "-i",
        str(video_path),
        "-an",
        "-vf",
        f"select='gt(scene,{scene_threshold})',showinfo,scale=1280:-1",
        "-vsync",
        "vfr",
        "-compression_level",
        "3",
        out_pattern,
    ]

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise VideoAnalysisError(f"ffmpeg frame extract failed: {proc.stderr.strip()}")

    pts_times: List[float] = []
    for line in (proc.stderr or "").splitlines():
        m = _SHOWINFO_PTS_RE.search(line)
        if m:
            pts_times.append(float(m.group("pts")))

    frame_paths = sorted(frames_dir.glob("frame_*.png"))
    if not frame_paths:
        return []

    # Map by index order; if showinfo count mismatches, keep timestamps as nulls.
    items: List[Dict[str, Any]] = []
    for idx, frame_path in enumerate(frame_paths):
        items.append(
            {
                "frame_path": str(frame_path),
                "timestamp": pts_times[idx] if idx < len(pts_times) else None,
            }
        )
    return items


def _extract_periodic_frames(
    ffmpeg: Path,
    video_path: Path,
    out_dir: Path,
    interval_seconds: int,
) -> List[Dict[str, Any]]:
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for existing in frames_dir.glob("frame_*"):
        try:
            existing.unlink()
        except OSError:
            pass
    out_pattern = str(frames_dir / "frame_%04d.png")

    fps = 1.0 / float(max(1, interval_seconds))
    cmd = [
        str(ffmpeg),
        "-y",
        "-i",
        str(video_path),
        "-an",
        "-vf",
        f"fps={fps},showinfo,scale=1280:-1",
        "-vsync",
        "vfr",
        "-compression_level",
        "3",
        out_pattern,
    ]

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise VideoAnalysisError(f"ffmpeg periodic frame extract failed: {proc.stderr.strip()}")

    pts_times: List[float] = []
    for line in (proc.stderr or "").splitlines():
        m = _SHOWINFO_PTS_RE.search(line)
        if m:
            pts_times.append(float(m.group("pts")))

    frame_paths = sorted(frames_dir.glob("frame_*.png"))
    if not frame_paths:
        return []

    items: List[Dict[str, Any]] = []
    for idx, frame_path in enumerate(frame_paths):
        items.append(
            {
                "frame_path": str(frame_path),
                "timestamp": pts_times[idx] if idx < len(pts_times) else None,
            }
        )
    return items


_SLIDE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "is_slide": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "title": {"type": ["string", "null"]},
        "extracted_text": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["is_slide", "confidence", "title", "extracted_text", "summary"],
}


def _analyze_frame_as_slide(
    client: OpenAI,
    model: str,
    temperature: float,
    frame_path: Path,
    usage_logger: UsageLogger | None = None,
) -> Dict[str, Any]:
    img_bytes = frame_path.read_bytes()
    b64 = base64.b64encode(img_bytes).decode("ascii")
    mime = "image/png" if frame_path.suffix.lower() == ".png" else "image/jpeg"
    data_url = f"data:{mime};base64,{b64}"

    prompt = (
        "You are extracting presentation slide content from a video frame.\n"
        "Return ONLY JSON that matches the provided schema.\n"
        "Guidance:\n"
        "- A 'slide' is a screen-captured or recorded presentation slide (mostly text/graphics on a flat background).\n"
        "- If it is not a slide (speaker, UI chrome, b-roll), set is_slide=false and keep other fields minimal.\n"
        "- extracted_text should include the readable text from the slide (best effort).\n"
        "- title should be the slide title if present.\n"
        "- confidence: your confidence that this frame is a slide.\n"
    )

    resp = client.responses.create(
        model=model,
        temperature=temperature,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "slide_extraction",
                "schema": _SLIDE_SCHEMA,
                "strict": True,
            }
        },
    )

    if usage_logger is not None:
        usage_logger.log(
            {
                "type": "openai_call",
                "ts": _utc_now_iso(),
                "kind": "vision_slide",
                "status": "ok",
                "model": model,
                "usage": _to_dict(resp.usage) if getattr(resp, "usage", None) is not None else None,
                "meta": {"frame_path": str(frame_path)},
            }
        )

    try:
        return json.loads(resp.output_text)
    except Exception as exc:  # pragma: no cover - defensive
        raise VideoAnalysisError(f"failed to parse slide JSON: {exc}") from exc


def _slug(text: str, max_len: int = 60) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip()).strip("-").lower()
    return cleaned[:max_len] if cleaned else "untitled"


_WS_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9 ]+")


def _norm_for_dedupe(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("•", " ").replace("–", "-").replace("—", "-")
    text = _WS_RE.sub(" ", text).strip()
    # Strip punctuation/quotes so formatting differences don't defeat dedupe.
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def _token_set(text: str) -> set[str]:
    normed = _norm_for_dedupe(text)
    return set(normed.split()) if normed else set()


def _dup_metrics(a_text: str, b_text: str) -> Tuple[float, float, float]:
    """Return (seq_ratio, jaccard, min_token_cover) for two texts."""
    a_norm = _norm_for_dedupe(a_text)
    b_norm = _norm_for_dedupe(b_text)
    if not a_norm or not b_norm:
        return (0.0, 0.0, 0.0)

    a_tokens = set(a_norm.split())
    b_tokens = set(b_norm.split())
    if not a_tokens or not b_tokens:
        return (0.0, 0.0, 0.0)

    inter = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    jacc = inter / union if union else 0.0
    min_cover = inter / min(len(a_tokens), len(b_tokens)) if min(len(a_tokens), len(b_tokens)) else 0.0
    seq = SequenceMatcher(None, a_norm, b_norm).ratio()
    return (seq, jacc, min_cover)


def _merge_duplicate_slides(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two slides that represent the same underlying slide.

    Heuristic: prefer a title if either has one; prefer the "cleaner" extracted_text
    when one text is a near-subset of the other; otherwise prefer the higher-confidence
    slide and longer extracted text.
    """
    a_title = (a.get("title") or "").strip()
    b_title = (b.get("title") or "").strip()

    a_text = a.get("extracted_text") or ""
    b_text = b.get("extracted_text") or ""
    a_tokens = _token_set(a_text)
    b_tokens = _token_set(b_text)
    inter = len(a_tokens & b_tokens)

    a_conf = float(a.get("confidence") or 0.0)
    b_conf = float(b.get("confidence") or 0.0)

    def pick_text() -> Tuple[str, str]:
        # Return (text, which) where which is "a" or "b".
        # If one token set is (almost) fully contained in the other, prefer the shorter text (less noisy),
        # unless it's extremely short.
        if a_tokens and b_tokens:
            a_in_b = inter / len(a_tokens) if a_tokens else 0.0
            b_in_a = inter / len(b_tokens) if b_tokens else 0.0
            if a_in_b >= 0.98 and b_in_a < 0.98:
                if len(a_tokens) >= 12:
                    return (a_text, "a")
            if b_in_a >= 0.98 and a_in_b < 0.98:
                if len(b_tokens) >= 12:
                    return (b_text, "b")
        # Otherwise prefer higher confidence, then longer text.
        if (b_conf, len(b_text)) > (a_conf, len(a_text)):
            return (b_text, "b")
        return (a_text, "a")

    merged: Dict[str, Any] = dict(a)
    merged["confidence"] = max(a_conf, b_conf)

    # Choose best title (prefer shorter non-empty).
    titles = [t for t in [a_title, b_title] if t]
    merged["title"] = min(titles, key=len) if titles else None

    chosen_text, chosen_src = pick_text()
    merged["extracted_text"] = chosen_text
    if chosen_src == "b":
        # Keep frame + summary aligned with chosen text when possible.
        merged["frame_path"] = b.get("frame_path", merged.get("frame_path"))
        merged["summary"] = b.get("summary", merged.get("summary"))
    else:
        merged["frame_path"] = a.get("frame_path", merged.get("frame_path"))
        merged["summary"] = a.get("summary", merged.get("summary"))

    # Prefer earliest timestamp for ordering.
    a_ts = a.get("timestamp")
    b_ts = b.get("timestamp")
    if isinstance(a_ts, (int, float)) and isinstance(b_ts, (int, float)):
        merged["timestamp"] = min(float(a_ts), float(b_ts))
    else:
        merged["timestamp"] = a_ts if a_ts is not None else b_ts

    return merged


def _dedupe_slides(
    slides: List[Dict[str, Any]],
    *,
    window_seconds: int = 180,
    min_token_cover: float = 0.95,
    min_seq_ratio: float = 0.985,
    min_jaccard_if_title_matches: float = 0.85,
) -> List[Dict[str, Any]]:
    """Dedupe slides where OCR text varies but the slide content is the same."""
    slides = sorted(slides, key=lambda s: float(s.get("timestamp") or 0.0))
    kept: List[Dict[str, Any]] = []

    for slide in slides:
        ts = float(slide.get("timestamp") or 0.0)

        match_idx: int | None = None
        for idx in range(len(kept) - 1, -1, -1):
            prev = kept[idx]
            prev_ts = float(prev.get("timestamp") or 0.0)
            if ts - prev_ts > float(window_seconds):
                break

            prev_title = (prev.get("title") or "").strip().lower()
            cur_title = (slide.get("title") or "").strip().lower()
            title_matches = bool(prev_title and cur_title and prev_title == cur_title)

            seq, jacc, min_cover = _dup_metrics(prev.get("extracted_text") or "", slide.get("extracted_text") or "")

            is_dup = (
                min_cover >= float(min_token_cover)
                or seq >= float(min_seq_ratio)
                or (title_matches and jacc >= float(min_jaccard_if_title_matches))
            )

            if is_dup:
                match_idx = idx
                break

        if match_idx is None:
            kept.append(slide)
        else:
            kept[match_idx] = _merge_duplicate_slides(kept[match_idx], slide)

    return kept


def _even_sample(items: List[Any], max_items: int) -> List[Any]:
    if max_items <= 0 or len(items) <= max_items:
        return items
    step = len(items) / float(max_items)
    indices = []
    used = set()
    for i in range(max_items):
        idx = int(i * step)
        if idx >= len(items):
            idx = len(items) - 1
        if idx in used:
            continue
        used.add(idx)
        indices.append(idx)
    if (len(items) - 1) not in used:
        indices.append(len(items) - 1)
    return [items[i] for i in sorted(indices)]


def analyze_video(
    video_path: str,
    output_dir: str | None = None,
    *,
    transcribe_model: str = "whisper-1",
    vision_model: str = "gpt-4.1",
    vision_temperature: float = 0.0,
    chunk_seconds: int = 600,
    scene_threshold: float = 0.30,
    max_frames: int = 80,
    fallback_interval_seconds: int = 10,
    dedupe_window_seconds: int = 180,
    dedupe_min_token_cover: float = 0.95,
    dedupe_min_seq_ratio: float = 0.985,
    max_slides: int = 15,
    slide_confidence_threshold: float = 0.60,
    keep_intermediate: bool = False,
    log_usage: bool = False,
    usage_log_path: str | None = None,
) -> Dict[str, Any]:
    """Analyze a local video file.

    Returns a JSON-serializable dict with output file paths and extracted slides.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise VideoAnalysisError("OPENAI_API_KEY is not set")

    video = Path(video_path).expanduser().resolve()
    if not video.is_file():
        raise VideoAnalysisError(f"video not found: {video}")

    out_root = Path(output_dir).expanduser().resolve() if output_dir else (Path.cwd() / f"{video.stem}_analysis")
    out_root.mkdir(parents=True, exist_ok=True)

    bins = ensure_ffmpeg()

    client = OpenAI(api_key=api_key)

    enable_usage = bool(log_usage or usage_log_path)
    usage_path: Path | None = None
    if enable_usage:
        usage_path = Path(usage_log_path) if usage_log_path else (out_root / "openai_usage.jsonl")
        if not usage_path.is_absolute():
            usage_path = out_root / usage_path

    usage_logger: UsageLogger | None = UsageLogger.open(usage_path) if usage_path is not None else None
    if usage_logger is not None:
        usage_logger.log(
            {
                "type": "run",
                "event": "start",
                "ts": _utc_now_iso(),
                "meta": {
                    "video_path": str(video),
                    "output_dir": str(out_root),
                    "transcribe_model": transcribe_model,
                    "vision_model": vision_model,
                    "vision_temperature": vision_temperature,
                    "chunk_seconds": chunk_seconds,
                    "scene_threshold": scene_threshold,
                    "max_frames": max_frames,
                    "fallback_interval_seconds": fallback_interval_seconds,
                },
            }
        )

    try:
        # 1) Transcript
        chunks = _extract_audio_chunks(bins.ffmpeg, video, out_root, chunk_seconds=chunk_seconds)
        transcript = _transcribe_chunks(
            client,
            chunks,
            model=transcribe_model,
            chunk_seconds=chunk_seconds,
            usage_logger=usage_logger,
        )

        transcript_json_path = out_root / "transcript.verbose.json"
        transcript_txt_path = out_root / "transcript.txt"
        transcript_srt_path = out_root / "transcript.srt"

        transcript_json_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        transcript_txt_path.write_text((transcript.get("text") or "").strip() + "\n", encoding="utf-8")
        _write_srt(transcript.get("segments") or [], transcript_srt_path)

        if not keep_intermediate:
            shutil.rmtree(out_root / "audio_chunks", ignore_errors=True)

        # 2) Slide candidates (scene changes)
        frames = _extract_scene_frames(bins.ffmpeg, video, out_root, scene_threshold=scene_threshold)
        if not frames:
            frames = _extract_periodic_frames(
                bins.ffmpeg,
                video,
                out_root,
                interval_seconds=fallback_interval_seconds,
            )
        frames = _even_sample(frames, max_frames)

        # 3) Vision extraction
        raw_slides: List[Dict[str, Any]] = []
        for item in frames:
            frame_path = Path(item["frame_path"])
            slide = _analyze_frame_as_slide(
                client,
                model=vision_model,
                temperature=vision_temperature,
                frame_path=frame_path,
                usage_logger=usage_logger,
            )
            slide["frame_path"] = str(frame_path)
            slide["timestamp"] = item.get("timestamp")
            raw_slides.append(slide)

        if keep_intermediate:
            (out_root / "slides.raw.json").write_text(
                json.dumps(raw_slides, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        slides = [
            s
            for s in raw_slides
            if bool(s.get("is_slide"))
            and float(s.get("confidence") or 0.0) >= float(slide_confidence_threshold)
        ]
        slides = _dedupe_slides(
            slides,
            window_seconds=dedupe_window_seconds,
            min_token_cover=dedupe_min_token_cover,
            min_seq_ratio=dedupe_min_seq_ratio,
        )
        slides = slides[:max_slides]

        key_dir = out_root / "key_slides"
        key_dir.mkdir(parents=True, exist_ok=True)
        # Keep key_slides consistent with slides.json on reruns.
        for existing in key_dir.glob("slide_*"):
            if existing.is_file():
                try:
                    existing.unlink()
                except OSError:
                    pass
        key_slides: List[Dict[str, Any]] = []
        for idx, slide in enumerate(slides, start=1):
            ts = slide.get("timestamp")
            ts_str = f"t{float(ts):07.2f}" if ts is not None else "tunknown"
            title = slide.get("title") or "untitled"
            fname = f"slide_{idx:02d}_{ts_str}_{_slug(title)}.png"
            dst = key_dir / fname
            shutil.copyfile(slide["frame_path"], dst)
            key_slides.append(
                {
                    "timestamp": ts,
                    "image_path": str(dst),
                    "title": slide.get("title"),
                    "extracted_text": slide.get("extracted_text", ""),
                    "summary": slide.get("summary", ""),
                    "confidence": slide.get("confidence", 0),
                }
            )

        slides_json_path = out_root / "slides.json"
        slides_json_path.write_text(json.dumps(key_slides, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        if not keep_intermediate:
            shutil.rmtree(out_root / "frames", ignore_errors=True)

        result = {
            "output_dir": str(out_root),
            "transcript_txt": str(transcript_txt_path),
            "transcript_srt": str(transcript_srt_path),
            "transcript_json": str(transcript_json_path),
            "slides_json": str(slides_json_path),
            "key_slides_dir": str(key_dir),
            "key_slides": key_slides,
            "usage_log_jsonl": str(usage_path) if usage_path is not None else None,
        }

        if usage_logger is not None:
            usage_logger.log(
                {
                    "type": "run",
                    "event": "end",
                    "ts": _utc_now_iso(),
                    "meta": {
                        "video_path": str(video),
                        "frames_analyzed": len(frames),
                        "slides_kept": len(key_slides),
                    },
                }
            )
        return result
    finally:
        if usage_logger is not None:
            usage_logger.close()
