"""Semantic-ish chunking by paragraph boundaries with word-count targets and overlap."""

from __future__ import annotations

import re
from typing import List, Optional

from .models import Chunk, ExtractedPDF


_PARA_SPLIT = re.compile(r"\n\s*\n")


def _split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in _PARA_SPLIT.split(text) if p.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_text(
    text: str,
    target_words: int = 1500,
    min_words: int = 1000,
    max_words: int = 2000,
    overlap_words: int = 150,
) -> List[Chunk]:
    """Chunk free text into ~1000-2000 word blocks, preferring paragraph boundaries."""
    if not text.strip():
        return []

    paragraphs = _split_paragraphs(text)
    chunks: List[Chunk] = []

    buf: List[str] = []
    buf_words = 0

    def flush() -> None:
        nonlocal buf, buf_words
        if not buf:
            return
        chunk_text_str = "\n\n".join(buf).strip()
        chunks.append(
            Chunk(
                chunk_id=len(chunks) + 1,
                text=chunk_text_str,
                word_count=_word_count(chunk_text_str),
            )
        )
        # Build overlap tail from the last `overlap_words` words.
        if overlap_words > 0:
            tail_words = chunk_text_str.split()[-overlap_words:]
            buf = [" ".join(tail_words)] if tail_words else []
            buf_words = len(tail_words)
        else:
            buf = []
            buf_words = 0

    for para in paragraphs:
        pw = _word_count(para)

        # Oversized paragraph: hard-split by sentences/words.
        if pw > max_words:
            words = para.split()
            for i in range(0, len(words), target_words):
                piece = " ".join(words[i : i + target_words])
                buf.append(piece)
                buf_words += _word_count(piece)
                if buf_words >= target_words:
                    flush()
            continue

        if buf_words + pw > max_words and buf_words >= min_words:
            flush()

        buf.append(para)
        buf_words += pw

        if buf_words >= target_words:
            flush()

    if buf_words > 0:
        # Merge a tiny trailing chunk into the previous one if possible.
        if chunks and buf_words < min_words // 2:
            last = chunks[-1]
            merged = (last.text + "\n\n" + "\n\n".join(buf)).strip()
            chunks[-1] = Chunk(
                chunk_id=last.chunk_id,
                text=merged,
                word_count=_word_count(merged),
                start_page=last.start_page,
                end_page=last.end_page,
            )
            buf, buf_words = [], 0
        else:
            flush()

    return chunks


def chunk_extracted_pdf(
    pdf: ExtractedPDF,
    target_words: int = 1500,
    min_words: int = 1000,
    max_words: int = 2000,
    overlap_words: int = 150,
) -> List[Chunk]:
    """Chunk an ExtractedPDF and best-effort tag chunks with start/end page numbers."""
    # Build text with page markers we can map back to page numbers.
    markers: List[tuple[int, str]] = []  # (page_number, text)
    for page in pdf.pages:
        markers.append((page.page_number, page.text))

    full = "\n\n".join(t for _, t in markers)
    chunks = chunk_text(
        full,
        target_words=target_words,
        min_words=min_words,
        max_words=max_words,
        overlap_words=overlap_words,
    )

    # Crude mapping: locate chunk text in concatenated string by character offset.
    page_offsets: List[tuple[int, int]] = []  # (page_number, end_offset)
    offset = 0
    for page_number, text in markers:
        offset += len(text) + 2  # account for "\n\n" join
        page_offsets.append((page_number, offset))

    cursor = 0
    for ch in chunks:
        idx = full.find(ch.text[:120], cursor) if ch.text else -1
        if idx < 0:
            continue
        start = idx
        end = idx + len(ch.text)
        cursor = max(cursor, start)
        ch.start_page = _offset_to_page(page_offsets, start)
        ch.end_page = _offset_to_page(page_offsets, end)

    return chunks


def _offset_to_page(page_offsets: List[tuple[int, int]], offset: int) -> Optional[int]:
    for page_number, end in page_offsets:
        if offset <= end:
            return page_number
    return page_offsets[-1][0] if page_offsets else None
