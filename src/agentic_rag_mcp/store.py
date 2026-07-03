"""pgvector-backed document store (Postgres / Supabase)."""

from __future__ import annotations

import json
from typing import Any

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

from .config import settings
from .embeddings import embed_documents, embed_query


def _connect() -> psycopg.Connection:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set — cannot reach the vector store.")
    conn = psycopg.connect(settings.database_url)
    register_vector(conn)
    return conn


def add_chunks(chunks: list[str], source: str, metadata: dict | None = None) -> int:
    """Embed and insert text chunks. Returns the number stored."""
    chunks = [c for c in (s.strip() for s in chunks) if c]
    if not chunks:
        return 0
    vectors = embed_documents(chunks)
    payload = json.dumps(metadata or {})
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO documents (content, embedding, source, metadata) "
                "VALUES (%s, %s, %s, %s::jsonb)",
                [
                    (text, Vector(vec), source, payload)
                    for text, vec in zip(chunks, vectors, strict=True)
                ],
            )
        conn.commit()
    return len(chunks)


def add_documents(items: list[tuple[str, str]]) -> int:
    """Embed and insert (content, source) pairs in a SINGLE embedding request.

    Used for bulk seeding (e.g. the eval corpus) so many small files cost one Voyage
    call instead of one per file — important on rate-limited tiers.
    """
    rows = [(c.strip(), s) for c, s in items if c and c.strip()]
    if not rows:
        return 0
    vectors = embed_documents([c for c, _ in rows])
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO documents (content, embedding, source, metadata) "
                "VALUES (%s, %s, %s, %s::jsonb)",
                [
                    (content, Vector(vec), source, json.dumps({"source": source}))
                    for (content, source), vec in zip(rows, vectors, strict=True)
                ],
            )
        conn.commit()
    return len(rows)


def search(query: str, k: int = 5) -> list[dict[str, Any]]:
    """Return the top-k most similar chunks (cosine similarity)."""
    qvec = Vector(embed_query(query))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content, source, metadata, "
                "1 - (embedding <=> %s) AS score "
                "FROM documents "
                "ORDER BY embedding <=> %s "
                "LIMIT %s",
                (qvec, qvec, k),
            )
            rows = cur.fetchall()
    return [
        {
            "id": str(r[0]),
            "content": r[1],
            "source": r[2],
            "metadata": r[3],
            "score": round(float(r[4]), 4),
        }
        for r in rows
    ]
