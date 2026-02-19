"""Speaker diarisation using pyannote-audio.

Prototype-mode implementation. Supports both the free community-1 model
(runs locally) and the premium precision-2 model (runs on pyannoteAI servers).
Optional LLM-based speaker identification maps SPEAKER_XX labels to real names.
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
# Speaker identification via LLM
# ---------------------------------------------------------------------------


def _identify_speakers_llm(
    segments: List[Dict[str, Any]],
    speakers: List[str],
    *,
    openai_api_key: str | None = None,
    model: str = "gpt-4.1-mini",
    context_hint: str | None = None,
) -> Dict[str, str]:
    """Use an LLM to map SPEAKER_XX labels to real names.

    Analyses the diarised transcript for contextual clues — introductions,
    hand-overs, slide titles mentioning names — and returns a mapping of
    ``{SPEAKER_XX: "Name, Role"}`` for every speaker it can identify.
    """
    api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {}

    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        return {}

    # Build a condensed transcript excerpt — first ~8000 chars of diarised text
    # plus the last ~2000 chars (where wrap-up/handovers happen).
    lines: List[str] = []
    char_count = 0
    for seg in segments:
        speaker = seg.get("speaker") or "UNKNOWN"
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = seg.get("start", 0)
        m, s = divmod(int(start), 60)
        line = f"[{speaker}] ({m}:{s:02d}) {text}"
        lines.append(line)
        char_count += len(line)
        if char_count > 8000:
            break

    # Also grab tail of transcript
    tail_lines: List[str] = []
    tail_chars = 0
    for seg in reversed(segments):
        speaker = seg.get("speaker") or "UNKNOWN"
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = seg.get("start", 0)
        m, s = divmod(int(start), 60)
        line = f"[{speaker}] ({m}:{s:02d}) {text}"
        tail_lines.insert(0, line)
        tail_chars += len(line)
        if tail_chars > 2000:
            break

    excerpt = "\n".join(lines)
    if tail_lines and tail_lines[0] != lines[-1]:
        excerpt += "\n\n[... later in the recording ...]\n\n" + "\n".join(tail_lines)

    context_section = ""
    if context_hint:
        context_section = f"\n\nAdditional context provided by the user:\n{context_hint}\n"

    system_prompt = (
        "You are an expert at identifying speakers from transcripts. "
        "You will be given a diarised transcript where speakers are labelled "
        "SPEAKER_00, SPEAKER_01 etc. Your task is to identify the real names "
        "of as many speakers as possible.\n\n"
        "Look for clues such as:\n"
        "- Self-introductions ('I'm X', 'My name is X')\n"
        "- Hand-overs ('Let me hand over to X', 'Over to you X', 'Thank you X')\n"
        "- Third-person references ('As X mentioned', 'X will present')\n"
        "- Context about roles/titles mentioned near speaker changes\n\n"
        "Return ONLY a JSON object mapping speaker IDs to names. "
        "Include a role/title if identifiable. For speakers you cannot identify, "
        "do not include them in the output.\n\n"
        "Example output:\n"
        '{"SPEAKER_00": "Jane Smith, CEO", "SPEAKER_02": "John Doe, CFO"}\n\n'
        "Return ONLY the JSON object, no other text."
    )

    user_prompt = (
        f"Here are the speaker labels found: {', '.join(speakers)}\n"
        f"{context_section}\n"
        f"Diarised transcript excerpt:\n\n{excerpt}"
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        mapping = json.loads(raw)
        # Validate: keys must be in speakers list, values must be strings
        return {k: str(v) for k, v in mapping.items() if k in speakers and v}
    except Exception:
        return {}


def _apply_speaker_map(
    segments: List[Dict[str, Any]],
    speaker_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Replace SPEAKER_XX labels with real names where identified."""
    result = []
    for seg in segments:
        seg = dict(seg)
        speaker = seg.get("speaker")
        if speaker and speaker in speaker_map:
            seg["speaker"] = speaker_map[speaker]
            seg["speaker_id"] = speaker  # preserve original ID
        result.append(seg)
    return result


# ---------------------------------------------------------------------------
# Illustrated markdown rendering
# ---------------------------------------------------------------------------


def _fmt_abs_time(seconds: float, clip_offset: float = 0.0) -> str:
    total = int(seconds + clip_offset)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def _render_illustrated_markdown(
    segments: List[Dict[str, Any]],
    slides: List[Dict[str, Any]],
    out_path: Path,
    *,
    title: str | None = None,
    clip_offset: float = 0.0,
    slides_base_dir: str | None = None,
) -> None:
    """Render an illustrated markdown transcript with slides inline.

    *slides* is the list from slides.json (each with timestamp, image_path,
    title, extracted_text, summary).  Slides are inserted between transcript
    paragraphs at the point matching their timestamp.

    *clip_offset* shifts all timestamps (e.g., 1800 if the clip starts at 30:00
    in the original recording).

    *slides_base_dir* controls how slide image paths are written.  When set,
    image_path is made relative to this directory.  Otherwise the path from
    slides.json is used as-is.
    """
    slides = sorted(slides, key=lambda s: s.get("timestamp", 0))

    md: List[str] = []
    if title:
        md.append(f"# {title}")
    else:
        md.append("# Diarised Transcript")
    md.append("")
    md.append("---")
    md.append("")

    slide_idx = 0
    current_speaker: str | None = None
    current_para: List[str] = []

    def flush_para() -> None:
        if current_para:
            md.append(" ".join(current_para))
            md.append("")
        current_para.clear()

    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        seg_start = float(seg.get("start", 0))

        # Insert slides whose timestamp falls before this segment
        while slide_idx < len(slides) and slides[slide_idx].get("timestamp", 0) < seg_start:
            flush_para()
            slide = slides[slide_idx]
            slide_ts = slide.get("timestamp", 0)
            slide_title = slide.get("title") or "(slide)"

            # Resolve image path
            img_path = slide.get("image_path", "")
            if slides_base_dir and img_path:
                try:
                    img_path = str(Path(img_path).relative_to(slides_base_dir))
                except ValueError:
                    pass  # keep absolute

            md.append("---")
            md.append("")
            md.append(
                f"> **📊 {slide_title}** `{_fmt_abs_time(slide_ts, clip_offset)}`"
            )
            md.append(">")
            md.append(f"> ![{slide_title}]({img_path})")
            extracted = slide.get("extracted_text")
            if extracted:
                flat = extracted.replace("\n", " · ")
                md.append(">")
                md.append(f"> *{flat}*")
            md.append("")
            md.append("---")
            md.append("")
            current_speaker = None  # force new header after slide
            slide_idx += 1

        # Speaker change?
        speaker = seg.get("speaker") or "UNKNOWN"
        if speaker != current_speaker:
            flush_para()
            current_speaker = speaker
            md.append(f"**{current_speaker}** `{_fmt_abs_time(seg_start, clip_offset)}`")
            md.append("")

        # Accumulate text, flush at sentence boundaries every ~400 chars
        current_para.append(text)
        joined = " ".join(current_para)
        if joined.endswith((".", "?", "!")) and len(joined) > 400:
            md.append(joined)
            md.append("")
            current_para.clear()

    flush_para()

    # Remaining slides after all segments
    while slide_idx < len(slides):
        slide = slides[slide_idx]
        slide_title = slide.get("title") or "(slide)"
        img_path = slide.get("image_path", "")
        if slides_base_dir and img_path:
            try:
                img_path = str(Path(img_path).relative_to(slides_base_dir))
            except ValueError:
                pass
        md.append(
            f"> **📊 {slide_title}** `{_fmt_abs_time(slide.get('timestamp', 0), clip_offset)}`"
        )
        md.append(f"> ![{slide_title}]({img_path})")
        md.append("")
        slide_idx += 1

    out_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")


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
    identify_speakers: bool = False,
    context_hint: str | None = None,
    slides_json: str | None = None,
    render_markdown: bool = False,
    markdown_title: str | None = None,
    clip_offset: float = 0.0,
) -> Dict[str, Any]:
    """Perform speaker diarisation on an audio or video file.

    Returns timestamped speaker turns. If *transcript_json* is provided
    (a ``transcript.verbose.json`` from ``media.analyze_video``), the
    output also includes speaker-attributed transcript segments and SRT.

    If *identify_speakers* is True and *transcript_json* is provided,
    uses an LLM (OpenAI) to map SPEAKER_XX labels to real names from
    contextual clues in the transcript. *context_hint* provides optional
    additional context (e.g., event name, known speakers).

    If *render_markdown* is True and *transcript_json* is provided,
    produces an illustrated markdown file with slide images inserted
    inline at the correct timestamps. Requires *slides_json* (path to
    ``slides.json`` from ``media.analyze_video``). *clip_offset* shifts
    displayed timestamps (e.g., 3600 if the clip starts at 1:00:00).
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
    enriched_segments: List[Dict[str, Any]] | None = None
    speaker_map: Dict[str, str] = {}

    if transcript_json:
        tj = Path(transcript_json).expanduser().resolve()
        if not tj.is_file():
            raise DiarizeError(f"transcript_json not found: {tj}")

        transcript = json.loads(tj.read_text(encoding="utf-8"))
        segments = transcript.get("segments") or []

        enriched_segments = _assign_speakers_to_segments(segments, turns)

        # --- Optional speaker identification ---
        if identify_speakers:
            speaker_map = _identify_speakers_llm(
                enriched_segments,
                speakers,
                context_hint=context_hint,
            )
            if speaker_map:
                enriched_segments = _apply_speaker_map(enriched_segments, speaker_map)
                # Also update turns with named speakers
                for t in turns:
                    if t["speaker"] in speaker_map:
                        t["speaker_name"] = speaker_map[t["speaker"]]

        diarized_transcript = {
            "text": transcript.get("text", ""),
            "segments": enriched_segments,
            "speakers": speakers,
            "speaker_map": speaker_map if speaker_map else None,
        }
        diarized_transcript_path = out_root / "transcript.diarized.json"
        diarized_transcript_path.write_text(
            json.dumps(diarized_transcript, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        diarized_srt_path = out_root / "transcript.diarized.srt"
        _write_diarized_srt(enriched_segments, diarized_srt_path)

    # --- Write speaker_map.json if we identified speakers ---
    speaker_map_path: Path | None = None
    if speaker_map:
        speaker_map_path = out_root / "speaker_map.json"
        speaker_map_path.write_text(
            json.dumps(speaker_map, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # --- Optional illustrated markdown ---
    markdown_path: Path | None = None
    if render_markdown and transcript_json and enriched_segments is not None:
        slides: List[Dict[str, Any]] = []
        if slides_json:
            sj = Path(slides_json).expanduser().resolve()
            if sj.is_file():
                slides = json.loads(sj.read_text(encoding="utf-8"))

        markdown_path = out_root / "transcript.md"
        _render_illustrated_markdown(
            enriched_segments,
            slides,
            markdown_path,
            title=markdown_title,
            clip_offset=clip_offset,
            slides_base_dir=str(out_root),
        )

    return {
        "output_dir": str(out_root),
        "turns": turns,
        "speakers": speakers,
        "speaker_map": speaker_map if speaker_map else None,
        "diarization_json": str(diarization_json_path),
        "diarized_transcript_json": str(diarized_transcript_path)
        if diarized_transcript_path
        else None,
        "diarized_srt": str(diarized_srt_path) if diarized_srt_path else None,
        "markdown": str(markdown_path) if markdown_path else None,
    }
