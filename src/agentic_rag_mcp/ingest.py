"""Ingestion: chunk text and store it in the vector store."""

from __future__ import annotations

from . import store, web


def chunk_text(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    """Split text into overlapping character windows on paragraph boundaries."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        # Prefer to break on a paragraph/newline boundary near the window end.
        if end < len(text):
            boundary = text.rfind("\n", start, end)
            if boundary > start + size // 2:
                end = boundary
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def ingest_text(text: str, source: str, metadata: dict | None = None) -> int:
    """Chunk raw text and store it. Returns the number of chunks stored."""
    return store.add_chunks(chunk_text(text), source=source, metadata=metadata)


def ingest_url(url: str) -> int:
    """Scrape a URL (Firecrawl), chunk it, and store it."""
    markdown = web.scrape(url)
    return store.add_chunks(chunk_text(markdown), source=url, metadata={"url": url})
