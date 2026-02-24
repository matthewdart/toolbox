# media.convert_eps_to_svg

Convert an EPS (Encapsulated PostScript) file to SVG using Inkscape CLI.

## Prerequisites

- **Inkscape** must be installed and available on `PATH`.
  - Docker: included in the toolbox image (`apt-get install inkscape`).
  - macOS: `brew install --cask inkscape`
  - Linux: `apt-get install inkscape`

## Usage

```python
from capabilities.media_convert_eps_to_svg.implementation import convert_eps_to_svg

result = convert_eps_to_svg(eps_path="/path/to/file.eps")
# {
#   "output_path": "/path/to/file.svg",
#   "file_size_bytes": 12345,
#   "inkscape_stderr": ""
# }
```

## Inputs

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `eps_path` | string | yes | | Path to the input EPS file |
| `output_path` | string\|null | no | `<stem>.svg` | Path for the output SVG |

## Outputs

| Field | Type | Description |
|---|---|---|
| `output_path` | string | Absolute path to the written SVG |
| `file_size_bytes` | integer | Size of the output SVG in bytes |
| `inkscape_stderr` | string | Inkscape stderr output (warnings/info) |

## Lifecycle

**Experimental** (Prototype Mode)
