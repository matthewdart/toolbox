# media.diarize_audio

Speaker diarisation using [pyannote-audio](https://github.com/pyannote/pyannote-audio). Identifies who spoke when in an audio or video file.

## Models

| Pipeline | Execution | Auth |
|---|---|---|
| `pyannote/speaker-diarization-community-1` | Local (GPU recommended) | HuggingFace token (`HF_TOKEN`) |
| `pyannote/speaker-diarization-precision-2` | pyannoteAI cloud | pyannoteAI API key (`PYANNOTE_API_KEY`) |

## Install

```bash
pip install pyannote-audio
```

## Usage

### Standalone diarisation

```python
from capabilities.media_diarize_audio.implementation import diarize_audio

result = diarize_audio("webcast.mp4", num_speakers=3)
for turn in result["turns"]:
    print(f"{turn['start']:.1f}s - {turn['end']:.1f}s: {turn['speaker']}")
```

### Composing with media.analyze_video

Run transcription first, then diarize and merge:

```python
from capabilities.media_analyze_video.implementation import analyze_video
from capabilities.media_diarize_audio.implementation import diarize_audio

# Step 1: Transcribe + extract slides
analysis = analyze_video("webcast.mp4")

# Step 2: Diarize and merge with transcript
result = diarize_audio(
    "webcast.mp4",
    transcript_json=analysis["transcript_json"],
    num_speakers=4,
)

# Result includes speaker-attributed transcript
print(result["diarized_srt"])       # SRT with [SPEAKER_00]: prefixes
print(result["diarized_transcript_json"])  # Whisper segments + speaker field
```

## Outputs

- `diarization.json` — raw speaker turns with timestamps
- `transcript.diarized.json` — Whisper segments enriched with `speaker` field (when `transcript_json` provided)
- `transcript.diarized.srt` — SRT subtitles with speaker labels (when `transcript_json` provided)

## Lifecycle

**Experimental** (Prototype Mode). No stability guarantees.
