---
name: download-video
description: Download a video from a URL to a local file using yt-dlp (supports many platforms) and return resolved file paths + metadata.
---

# Download Video

Download a video from a URL to a local file using yt-dlp (supports many platforms) and return resolved file paths + metadata.

## Invocation

Call the `media.download_video` capability via MCP:

```
media.download_video(url="...")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | yes | — | Video page URL or direct media URL. |
| `output_dir` | string? | no | — | Directory where downloads are written. Defaults to ./downloads. |
| `filename_template` | string? | no | — | Optional yt-dlp output template (e.g. "%(title)s [%(id)s].%(ext)s"). If null, a default template is used. |
| `format` | string | no | `"bestvideo+bestaudio/best"` | yt-dlp format selector. |
| `cookies_path` | string? | no | — | Optional path to a Netscape-format cookies.txt file for authenticated downloads. |
| `headers` | object? | no | — | Optional HTTP headers to send. Values must be strings. |
| `user_agent` | string? | no | — | Convenience: set the User-Agent header. |
| `referer` | string? | no | — | Convenience: set the Referer header. |
| `allow_playlist` | boolean | no | `false` | Allow downloading playlist/multi-entry pages. |
| `download` | boolean | no | `true` | If false, only extract metadata (no download). |
| `overwrite` | boolean | no | `false` | If true, overwrite existing files. |
| `quiet` | boolean | no | `false` | Reduce downloader output. |
| `write_info_json` | boolean | no | `true` | When true, write a JSON metadata file to output_dir. |
| `live_from_start` | boolean | no | `false` | Record live streams from the beginning instead of the current position (requires DVR/rewind support from the platform). |
| `wait_for_video` | boolean | no | `false` | Wait for scheduled/upcoming live streams to start before downloading. |

## Error Codes

| Code | Description |
|------|-------------|
| `validation_error` | Input did not match schema. |
| `output_validation_error` | Output did not match schema. |
| `capability_error` | Download failed (missing yt-dlp, auth required, DRM, network errors, etc.). |

## Side Effects

Performs network calls to fetch video metadata and optionally downloads media files to output_dir; may write an info.json file when write_info_json=true.
