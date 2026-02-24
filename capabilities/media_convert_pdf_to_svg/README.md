# media.convert_pdf_to_svg

Convert a page from a PDF file to SVG using Inkscape CLI.

Inkscape's PDF import preserves vector paths, text, and structure well. Use in combination with `media.render_svg_to_png` for a full PDF → SVG → PNG pipeline.

## Prerequisites

- **Inkscape** must be installed and available on `PATH`.
  - Docker: included in the toolbox image.
  - macOS: `brew install --cask inkscape`
  - Linux: `apt-get install inkscape`

## Usage

```python
from capabilities.media_convert_pdf_to_svg.implementation import convert_pdf_to_svg

result = convert_pdf_to_svg(pdf_path="/path/to/file.pdf", page=2)
# {
#   "output_path": "/path/to/file.svg",
#   "file_size_bytes": 23456,
#   "page": 2,
#   "inkscape_stderr": ""
# }
```

## Inputs

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `pdf_path` | string | yes | | Path to the input PDF file |
| `output_path` | string\|null | no | `<stem>.svg` | Path for the output SVG |
| `page` | integer\|null | no | 1 | 1-based page number to convert |

## Outputs

| Field | Type | Description |
|---|---|---|
| `output_path` | string | Absolute path to the written SVG |
| `file_size_bytes` | integer | Size of the output SVG in bytes |
| `page` | integer | The 1-based page number that was converted |
| `inkscape_stderr` | string | Inkscape stderr output (warnings/info) |

## Lifecycle

**Experimental** (Prototype Mode)
