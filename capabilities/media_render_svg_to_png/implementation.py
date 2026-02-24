"""Render SVG to PNG using Inkscape CLI."""

from __future__ import annotations

import shutil
import struct
import subprocess
from pathlib import Path
from typing import Any, Dict


class RenderError(RuntimeError):
    """Raised when SVG-to-PNG rendering fails."""


def _read_png_dimensions(png_path: Path) -> tuple[int, int]:
    """Read width and height from a PNG file header (IHDR chunk).

    The PNG spec places width (4 bytes BE) at offset 16 and height at
    offset 20.  No external dependencies needed.
    """
    with png_path.open("rb") as fh:
        header = fh.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RenderError(f"Not a valid PNG file: {png_path}")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def render_svg_to_png(
    svg_path: str,
    output_path: str | None = None,
    width: int | None = None,
    height: int | None = None,
    dpi: int | None = None,
    background: str | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Render an SVG file to PNG using Inkscape.

    Returns a dict with the output path, dimensions, file size, and
    Inkscape stderr.
    """
    # --- Check Inkscape is available ---
    inkscape = shutil.which("inkscape")
    if not inkscape:
        raise RenderError(
            "inkscape not found in PATH. "
            "Install it with: apt-get install inkscape"
        )

    # --- Resolve input path ---
    svg = Path(svg_path).expanduser().resolve()
    if not svg.is_file():
        raise RenderError(f"SVG file not found: {svg}")
    if svg.suffix.lower() != ".svg":
        raise RenderError(f"Expected an SVG file, got: {svg.suffix!r}")

    # --- Resolve output path ---
    if output_path is not None:
        png = Path(output_path).expanduser().resolve()
    else:
        png = svg.with_suffix(".png")

    png.parent.mkdir(parents=True, exist_ok=True)

    # --- Build Inkscape command ---
    cmd = [
        inkscape,
        str(svg),
        "--export-filename=" + str(png),
        "--export-type=png",
    ]
    if width is not None:
        cmd.append(f"--export-width={width}")
    if height is not None:
        cmd.append(f"--export-height={height}")
    if dpi is not None:
        cmd.append(f"--export-dpi={dpi}")
    if background is not None:
        cmd.append(f"--export-background={background}")
        cmd.append("--export-background-opacity=1")

    # --- Run Inkscape ---
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
        raise RenderError(
            f"Inkscape exited with code {proc.returncode}: {detail}"
        )

    # --- Verify output ---
    if not png.is_file():
        raise RenderError(
            f"Inkscape reported success but output file not found: {png}"
        )

    width_px, height_px = _read_png_dimensions(png)

    return {
        "output_path": str(png),
        "width_px": width_px,
        "height_px": height_px,
        "file_size_bytes": png.stat().st_size,
        "inkscape_stderr": proc.stderr.strip(),
    }
