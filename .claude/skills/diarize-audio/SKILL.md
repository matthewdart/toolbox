---
name: diarize-audio
description: Perform speaker diarisation on an audio or video file using pyannote-audio, returning timestamped speaker turns. Optionally merge with a Whisper transcript to produce speaker-attributed segments.
---

# Diarize Audio

Perform speaker diarisation on an audio or video file using pyannote-audio, returning timestamped speaker turns. Optionally merge with a Whisper transcript to produce speaker-attributed segments.

## Invocation

Call the `media.diarize_audio` capability via MCP:

```
media.diarize_audio(audio_path="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `audio_path` | string | yes | — | Path to an audio or video file (any format readable by ffmpeg). |
| `model` | string | no | `"pyannote/speaker-diarization-community-1"` | Pyannote pipeline name. Use 'pyannote/speaker-diarization-community-1' (free, local) or 'pyannote/speaker-diarization-precision-2' (cloud API). |
| `token` | string? | no | — | HuggingFace token (for community models) or pyannoteAI API key (for precision models). Falls back to HF_TOKEN or PYANNOTE_API_KEY environment variables. |
| `num_speakers` | integer? | no | — | Exact number of speakers if known. |
| `min_speakers` | integer? | no | — | Minimum expected number of speakers. |
| `max_speakers` | integer? | no | — | Maximum expected number of speakers. |
| `device` | string? | no | — | PyTorch device for local models (e.g., 'cuda', 'cpu', 'mps'). Auto-detected if null. Ignored for cloud models. |
| `output_dir` | string? | no | — | Directory for output files. Defaults to ./<audio_stem>_diarization. |
| `transcript_json` | string? | no | — | Optional path to a transcript.verbose.json from media.analyze_video. When provided, output includes speaker-attributed transcript segments and SRT. |
| `identify_speakers` | boolean | no | `false` | When true and transcript_json is provided, use an LLM (OpenAI) to identify speaker names from contextual clues in the transcript (introductions, hand-overs, slide references). Requires OPENAI_API_KEY. |
| `context_hint` | string? | no | — | Optional context to help the LLM identify speakers (e.g., event name, known attendees, company). Only used when identify_speakers is true. |

## Error Codes

| Code | Description |
|------|-------------|
| `validation_error` | Input did not match schema. |
| `output_validation_error` | Output did not match schema. |
| `capability_error` | Diarisation failed (missing pyannote-audio, invalid token, audio unreadable, etc.). |

## Side Effects

Downloads pyannote model weights on first use (community models). Cloud models send audio to pyannoteAI servers. Writes output files to output_dir.
