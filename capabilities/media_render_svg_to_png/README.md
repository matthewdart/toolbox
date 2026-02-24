# media.render_svg_to_png

Render an SVG file to a PNG image using Inkscape CLI, with optional size, DPI, and background controls.

Designed as the rasterisation bridge for inserting vector content into surfaces that only accept raster images (e.g. PowerPoint via Office.js `addPicture`).

## Prerequisites

- **Inkscape** must be installed and available on `PATH`.
  - Docker: included in the toolbox image.
  - macOS: `brew install --cask inkscape`
  - Linux: `apt-get install inkscape`

## Usage

```python
from capabilities.media_render_svg_to_png.implementation import render_svg_to_png

result = render_svg_to_png(
    svg_path="/path/to/file.svg",
    width=960,
    background="#FFFFFF",
)
# {
#   "output_path": "/path/to/file.png",
#   "width_px": 960,
#   "height_px": 540,
#   "file_size_bytes": 45678,
#   "inkscape_stderr": ""
# }
```

## Inputs

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `svg_path` | string | yes | | Path to the input SVG file |
| `output_path` | string\|null | no | `<stem>.png` | Path for the output PNG |
| `width` | integer\|null | no | auto | Export width in pixels |
| `height` | integer\|null | no | auto | Export height in pixels |
| `dpi` | integer\|null | no | 96 | Export DPI |
| `background` | string\|null | no | transparent | Background colour as hex |

## Outputs

| Field | Type | Description |
|---|---|---|
| `output_path` | string | Absolute path to the written PNG |
| `width_px` | integer | Width of the rendered PNG in pixels |
| `height_px` | integer | Height of the rendered PNG in pixels |
| `file_size_bytes` | integer | Size of the output PNG in bytes |
| `inkscape_stderr` | string | Inkscape stderr output (warnings/info) |

## Lifecycle

**Experimental** (Prototype Mode)
