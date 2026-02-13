# Video: transcript + key slides (OpenAI)

This repo includes a prototype capability to:

- generate a transcript from a local video file
- extract key slide images + their text

It uses OpenAI APIs and requires `OPENAI_API_KEY`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Either set it in your shell:
export OPENAI_API_KEY="..."
#
# Or create a local `.env` (this repo ignores `.env*` via `.gitignore`):
cp .env.example .env
# then edit `.env` and set OPENAI_API_KEY=...
```

## Run (recommended)

```bash
.venv/bin/python scripts/analyze_video_openai.py /path/to/video.mp4
```

## Download first (optional)

If you have a webinar/video URL (not a local file yet), download it first:

```bash
.venv/bin/python -m core.dispatch --capability media.download_video --input-json '{"url":"https://example.com/video"}'
```

### Login-gated sites

For sites that require authentication (e.g. BrightTalk webinars), export browser cookies first using the `browser.export_cookies` capability, then pass the cookies file to the download:

```bash
# Export cookies from Safari for the target domain
.venv/bin/python -m core.dispatch --capability browser.export_cookies --input-json '{"browser":"safari","domain":"brighttalk.com","output":"/tmp/brighttalk.cookies.txt"}'

# Download using the exported cookies
.venv/bin/python -m core.dispatch --capability media.download_video --input-json '{"url":"https://example.com/video","cookies_path":"/tmp/brighttalk.cookies.txt"}'
```

> **Security note:** treat cookies.txt files like passwords. Do not commit them.

## Outputs

Outputs default to `./<video_stem>_analysis/`:

- `transcript.txt`
- `transcript.srt`
- `transcript.verbose.json`
- `slides.json`
- `key_slides/` (PNG images)
- `openai_usage.jsonl` (optional; enable with `--log-usage`)

## Run via dispatcher (contract-validated)

```bash
.venv/bin/python -m core.dispatch --capability media.analyze_video --input-json '{"video_path":"/path/to/video.mp4"}'
```

## Notes

- If `ffmpeg` is not installed, the capability uses `imageio-ffmpeg` to download a compatible ffmpeg binary. You can override by setting `FFMPEG_BIN`/`FFPROBE_BIN`.
- Defaults target "reasonable cost": extracted frames are sampled evenly and capped with `max_frames` before calling the vision model.
- Slide OCR stability: use a lower `--vision-temperature` (default `0.0`) and a stronger `--vision-model` (default `gpt-4.1`).
- Duplicate slides: tune `--dedupe-window-seconds`, `--dedupe-min-token-cover`, and `--dedupe-min-seq-ratio` if you see repeated slides due to multiple frames on the same slide.
- Reruns: `slides.json` is overwritten and `key_slides/slide_*` outputs from prior runs are removed so the folder matches the JSON.
- Cost/usage: run with `--log-usage` to produce `openai_usage.jsonl`, then use `openai.calculate_usage_cost` to summarize (and optionally estimate cost with a price table).
