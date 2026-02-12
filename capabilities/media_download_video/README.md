# media.download_video

## Description

Download a video from a URL to a local file using yt-dlp (supports many platforms) and return resolved file paths and metadata. Includes a BrightTALK fallback for unsupported URLs.

## Non-goals

- Video transcoding or format conversion
- Playlist management
- DRM circumvention
- Streaming playback

## Deterministic behavior

Given the same URL, parameters, and upstream availability, the capability downloads the same content. Metadata may vary if the upstream source changes.
