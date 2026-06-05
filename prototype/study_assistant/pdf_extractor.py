"""PDF text extraction.

Primary backend: PyMuPDF (fitz). Falls back to pdfplumber if requested.
Performs lightweight cleaning: removes repeated headers/footers, collapses
whitespace, and preserves page numbers.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import List, Literal

from .models import ExtractedPDF, Page

Backend = Literal["pymupdf", "pdfplumber"]


_WS_RE = re.compile(r"[ \t]+")
_NEWLINES_RE = re.compile(r"\n{3,}")


def _clean_line(line: str) -> str:
    line = line.replace("\u00ad", "")  # soft hyphen
    line = _WS_RE.sub(" ", line).strip()
    return line


def _detect_repeating_lines(pages_lines: List[List[str]], threshold: float = 0.6) -> set[str]:
    """Find lines that appear on a large fraction of pages (headers/footers)."""
    if not pages_lines:
        return set()
    counts: Counter[str] = Counter()
    for lines in pages_lines:
        # Only consider first/last 3 lines on each page as header/footer candidates.
        candidates = set(lines[:3] + lines[-3:])
        for line in candidates:
            if 0 < len(line) <= 120:
                counts[line] += 1
    n_pages = len(pages_lines)
    return {line for line, c in counts.items() if c / n_pages >= threshold}


def _extract_pymupdf(pdf_path: Path) -> List[List[str]]:
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    try:
        return [
            [_clean_line(l) for l in page.get_text("text").splitlines()]
            for page in doc
        ]
    finally:
        doc.close()


def _extract_pdfplumber(pdf_path: Path) -> List[List[str]]:
    import pdfplumber

    out: List[List[str]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            out.append([_clean_line(l) for l in text.splitlines()])
    return out


def extract_pdf_text(
    pdf_path: str | Path,
    backend: Backend = "pymupdf",
    drop_headers_footers: bool = True,
) -> ExtractedPDF:
    """Extract text from a PDF, preserving page numbers and cleaning artefacts."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    if backend == "pymupdf":
        pages_lines = _extract_pymupdf(pdf_path)
    elif backend == "pdfplumber":
        pages_lines = _extract_pdfplumber(pdf_path)
    else:
        raise ValueError(f"Unknown backend: {backend}")

    repeating = _detect_repeating_lines(pages_lines) if drop_headers_footers else set()

    pages: List[Page] = []
    for i, lines in enumerate(pages_lines, start=1):
        kept = [l for l in lines if l and l not in repeating]
        # Drop bare page numbers ("12", "Page 12", "12 of 300")
        kept = [
            l for l in kept
            if not re.fullmatch(r"(page\s+)?\d+(\s*(/|of)\s*\d+)?", l, re.IGNORECASE)
        ]
        text = "\n".join(kept)
        text = _NEWLINES_RE.sub("\n\n", text).strip()
        pages.append(Page(page_number=i, text=text))

    return ExtractedPDF(source_path=str(pdf_path), pages=pages)
