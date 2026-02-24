"""Convert EPS to SVG using Inkscape CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


class ConversionError(RuntimeError):
    """Raised when EPS-to-SVG conversion fails."""


def convert_eps_to_svg(
    eps_path: str,
    output_path: str | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Convert an EPS file to SVG using Inkscape.

    Returns a dict with the output path, file size, and Inkscape stderr.
    """
    # --- Check Inkscape is available ---
    inkscape = shutil.which("inkscape")
    if not inkscape:
        raise ConversionError(
            "inkscape not found in PATH. "
            "Install it with: apt-get install inkscape"
        )

    # --- Resolve input path ---
    eps = Path(eps_path).expanduser().resolve()
    if not eps.is_file():
        raise ConversionError(f"EPS file not found: {eps}")
    if eps.suffix.lower() not in (".eps", ".epsf", ".ps"):
        raise ConversionError(
            f"Expected an EPS file, got: {eps.suffix!r}"
        )

    # --- Resolve output path ---
    if output_path is not None:
        svg = Path(output_path).expanduser().resolve()
    else:
        svg = eps.with_suffix(".svg")

    svg.parent.mkdir(parents=True, exist_ok=True)

    # --- Run Inkscape ---
    cmd = [
        inkscape,
        str(eps),
        "--export-filename=" + str(svg),
        "--export-type=svg",
    ]

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
        raise ConversionError(
            f"Inkscape exited with code {proc.returncode}: {detail}"
        )

    # --- Verify output ---
    if not svg.is_file():
        raise ConversionError(
            f"Inkscape reported success but output file not found: {svg}"
        )

    return {
        "output_path": str(svg),
        "file_size_bytes": svg.stat().st_size,
        "inkscape_stderr": proc.stderr.strip(),
    }
