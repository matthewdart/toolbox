"""Speaker diarisation using pyannote-audio.

Prototype-mode implementation. Supports both the free community-1 model
(runs locally) and the premium precision-2 model (runs on pyannoteAI servers).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class DiarizeError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# SRT helpers (duplicated from media_analyze_video; prototype-mode acceptable)
# ---------------------------------------------------------------------------


def _format_srt_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, rem = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{rem:03d}"


def _write_diarized_srt(
    segments: List[Dict[str, Any]],
    path: Path,
) -> None:
    lines: List[str] = []
    for idx, seg in enumerate(segments, start=1):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        speaker = seg.get("speaker")
        prefix = f"[{speaker}]: " if speaker else ""
        lines.append(str(idx))
        lines.append(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(end)}")
        lines.append(f"{prefix}{text}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------


def _resolve_token(token: str | None, model: str) -> str | None:
    if token:
        return token
    # Cloud models use PYANNOTE_API_KEY; local models use HF_TOKEN.
    if "precision" in model:
        return os.environ.get("PYANNOTE_API_KEY")
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")


# ---------------------------------------------------------------------------
# Transcript merge
# ---------------------------------------------------------------------------


def _assign_speakers_to_segments(
    segments: List[Dict[str, Any]],
    turns: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Assign a speaker to each transcript segment using majority overlap."""
    enriched: List[Dict[str, Any]] = []
    for seg in segments:
        seg = dict(seg)  # shallow copy
        seg_start = float(seg.get("start", 0.0))
        seg_end = float(seg.get("end", seg_start))
        if seg_end <= seg_start:
            seg["speaker"] = None
            enriched.append(seg)
            continue

        best_speaker: str | None = None
        best_overlap = 0.0

        for turn in turns:
            t_start = turn["start"]
            t_end = turn["end"]
            overlap_start = max(seg_start, t_start)
            overlap_end = min(seg_end, t_end)
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = turn["speaker"]

        seg["speaker"] = best_speaker
        enriched.append(seg)

    return enriched


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def diarize_audio(
    audio_path: str,
    *,
    model: str = "pyannote/speaker-diarization-community-1",
    token: str | None = None,
    num_speakers: int | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
    device: str | None = None,
    output_dir: str | None = None,
    transcript_json: str | None = None,
) -> Dict[str, Any]:
    """Perform speaker diarisation on an audio or video file.

    Returns timestamped speaker turns. If *transcript_json* is provided
    (a ``transcript.verbose.json`` from ``media.analyze_video``), the
    output also includes speaker-attributed transcript segments and SRT.
    """
    try:
        from pyannote.audio import Pipeline  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise DiarizeError(
            "pyannote-audio is required. Install with: pip install pyannote-audio"
        ) from exc

    audio = Path(audio_path).expanduser().resolve()
    if not audio.is_file():
        raise DiarizeError(f"audio_path not found: {audio}")

    resolved_token = _resolve_token(token, model)

    # --- Load pipeline ---
    try:
        pipeline = Pipeline.from_pretrained(model, token=resolved_token)
    except Exception as exc:
        raise DiarizeError(f"failed to load pyannote pipeline '{model}': {exc}") from exc

    # Route to device for local models (cloud models ignore this).
    if device:
        try:
            import torch  # type: ignore

            pipeline.to(torch.device(device))
        except Exception:
            pass  # best-effort; cloud models don't support .to()
    elif "precision" not in model:
        # Auto-detect best available device for local models.
        try:
            import torch  # type: ignore

            if torch.cuda.is_available():
                pipeline.to(torch.device("cuda"))
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                pipeline.to(torch.device("mps"))
        except Exception:
            pass

    # --- Run diarisation ---
    pipeline_kwargs: Dict[str, Any] = {}
    if num_speakers is not None:
        pipeline_kwargs["num_speakers"] = int(num_speakers)
    if min_speakers is not None:
        pipeline_kwargs["min_speakers"] = int(min_speakers)
    if max_speakers is not None:
        pipeline_kwargs["max_speakers"] = int(max_speakers)

    try:
        output = pipeline(str(audio), **pipeline_kwargs)
    except Exception as exc:
        raise DiarizeError(f"diarisation failed: {exc}") from exc

    # --- Extract turns ---
    turns: List[Dict[str, Any]] = []
    speakers_set: set[str] = set()

    # pyannote v4 returns a DiarizeOutput dataclass; v3 returns Annotation directly
    annotation = getattr(output, "speaker_diarization", output)
    for turn, _, speaker in annotation.itertracks(yield_label=True):
        label = str(speaker)
        turns.append(
            {
                "start": round(float(turn.start), 3),
                "end": round(float(turn.end), 3),
                "speaker": label,
            }
        )
        speakers_set.add(label)

    speakers = sorted(speakers_set)

    # --- Output directory ---
    if output_dir:
        out_root = Path(output_dir).expanduser().resolve()
    else:
        out_root = audio.parent / f"{audio.stem}_diarization"
    out_root.mkdir(parents=True, exist_ok=True)

    # --- Write diarization.json ---
    diarization_data = {
        "audio_path": str(audio),
        "model": model,
        "speakers": speakers,
        "turns": turns,
    }
    diarization_json_path = out_root / "diarization.json"
    diarization_json_path.write_text(
        json.dumps(diarization_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- Optional transcript merge ---
    diarized_transcript_path: Path | None = None
    diarized_srt_path: Path | None = None

    if transcript_json:
        tj = Path(transcript_json).expanduser().resolve()
        if not tj.is_file():
            raise DiarizeError(f"transcript_json not found: {tj}")

        transcript = json.loads(tj.read_text(encoding="utf-8"))
        segments = transcript.get("segments") or []

        enriched_segments = _assign_speakers_to_segments(segments, turns)

        diarized_transcript = {
            "text": transcript.get("text", ""),
            "segments": enriched_segments,
            "speakers": speakers,
        }
        diarized_transcript_path = out_root / "transcript.diarized.json"
        diarized_transcript_path.write_text(
            json.dumps(diarized_transcript, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        diarized_srt_path = out_root / "transcript.diarized.srt"
        _write_diarized_srt(enriched_segments, diarized_srt_path)

    return {
        "output_dir": str(out_root),
        "turns": turns,
        "speakers": speakers,
        "diarization_json": str(diarization_json_path),
        "diarized_transcript_json": str(diarized_transcript_path)
        if diarized_transcript_path
        else None,
        "diarized_srt": str(diarized_srt_path) if diarized_srt_path else None,
    }
