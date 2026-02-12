# media.analyze_video

## Description

Transcribe a local video file and extract key slide images using OpenAI APIs (Whisper for audio, vision models for slide OCR).

## Non-goals

- Streaming or real-time video processing
- Video editing or re-encoding
- Slide layout or design analysis
- Speaker diarisation

## Deterministic behavior

Given the same video file and parameters, the transcript and slide extraction pipeline produces consistent results. Vision model outputs may vary slightly due to model non-determinism even at temperature 0.
