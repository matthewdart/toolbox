"""Convert a PDF page to SVG using Inkscape CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


class ConversionError(RuntimeError):
    """Raised when PDF-to-SVG conversion fails."""


def convert_pdf_to_svg(
    pdf_path: str,
    output_path: str | None = None,
    page: int | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Convert a page from a PDF file to SVG using Inkscape.

    Returns a dict with the output path, file size, page number, and
    Inkscape stderr.
    """
    # --- Check Inkscape is available ---
    inkscape = shutil.which("inkscape")
    if not inkscape:
        raise ConversionError(
            "inkscape not found in PATH. "
            "Install it with: apt-get install inkscape"
        )

    # --- Resolve input path ---
    pdf = Path(pdf_path).expanduser().resolve()
    if not pdf.is_file():
        raise ConversionError(f"PDF file not found: {pdf}")
    if pdf.suffix.lower() != ".pdf":
        raise ConversionError(f"Expected a PDF file, got: {pdf.suffix!r}")

    # --- Page number ---
    page_1based = page if page is not None else 1
    if page_1based < 1:
        raise ConversionError(f"Page number must be >= 1, got: {page_1based}")
    # Inkscape uses 0-based page indexing
    page_0based = page_1based - 1

    # --- Resolve output path ---
    if output_path is not None:
        svg = Path(output_path).expanduser().resolve()
    else:
        svg = pdf.with_suffix(".svg")

    svg.parent.mkdir(parents=True, exist_ok=True)

    # --- Build Inkscape command ---
    cmd = [
        inkscape,
        str(pdf),
        "--export-filename=" + str(svg),
        "--export-type=svg",
        f"--pdf-page={page_0based}",
    ]

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
        "page": page_1based,
        "inkscape_stderr": proc.stderr.strip(),
    }
