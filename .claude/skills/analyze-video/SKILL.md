---
name: analyze-video
description: Transcribe a local video file and extract key slide images using OpenAI APIs.
---

# Analyze Video

Transcribe a local video file and extract key slide images using OpenAI APIs.

## Invocation

Call the `media.analyze_video` capability via MCP:

```
media.analyze_video(video_path="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_path` | string | yes | — | Path to a local video file (e.g., .mp4). |
| `output_dir` | string? | no | — | Directory where outputs are written. Defaults to ./<video_stem>_analysis. |
| `transcribe_model` | string | no | `"whisper-1"` | OpenAI audio transcription model (e.g., whisper-1). |
| `vision_model` | string | no | `"gpt-4.1"` | OpenAI vision-capable model for slide extraction. |
| `vision_temperature` | number | no | `0` | Vision model temperature for slide OCR/extraction (lower = more deterministic). |
| `chunk_seconds` | integer | no | `600` | Audio chunk size in seconds (used to avoid file size limits). |
| `scene_threshold` | number | no | `0.3` | ffmpeg scene-change threshold (higher = fewer frames). |
| `max_frames` | integer | no | `80` | Maximum number of extracted frames to analyze with the vision model (frames are sampled evenly across the video if needed). |
| `fallback_interval_seconds` | integer | no | `10` | If no scene-change frames are found, sample one frame every N seconds. |
| `dedupe_window_seconds` | integer | no | `180` | Only consider frames within this time window (seconds) as potential duplicates. |
| `dedupe_min_token_cover` | number | no | `0.95` | Minimum token overlap (as a fraction of the shorter text) to treat two slides as duplicates. |
| `dedupe_min_seq_ratio` | number | no | `0.985` | Minimum normalized string similarity to treat two slides as duplicates. |
| `log_usage` | boolean | no | `false` | When true, write OpenAI per-call usage events to a JSONL file. |
| `usage_log_path` | string? | no | — | Optional path for the usage JSONL file. If relative, it is resolved under output_dir. If omitted and log_usage=true, defaults to <output_dir>/openai_usage.jsonl. |
| `max_slides` | integer | no | `15` | Maximum number of slides to keep after filtering/deduping. |
| `slide_confidence_threshold` | number | no | `0.6` | Minimum confidence for a frame to be treated as a slide. |
| `keep_intermediate` | boolean | no | `false` | Keep intermediate files (audio chunks / extracted frames). |

## Error Codes

| Code | Description |
|------|-------------|
| `validation_error` | Input did not match schema. |
| `output_validation_error` | Output did not match schema. |
| `capability_error` | Execution failed (missing ffmpeg, missing OPENAI_API_KEY, API error, etc.). |

## Side Effects

Performs network calls to OpenAI APIs; writes files under output_dir; overwrites transcript/slides outputs on rerun and removes prior key_slides/slide_* outputs; may download an ffmpeg binary via imageio-ffmpeg if ffmpeg is not present.
