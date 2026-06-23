"""Embeddings via Voyage AI (Anthropic's recommended embeddings partner)."""

from __future__ import annotations

from functools import lru_cache

import voyageai

from .config import settings


@lru_cache(maxsize=1)
def _client() -> voyageai.Client:
    return voyageai.Client(api_key=settings.voyage_api_key)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of documents for storage."""
    if not texts:
        return []
    result = _client().embed(
        texts,
        model=settings.embed_model,
        input_type="document",
        output_dimension=settings.embed_dim,
    )
    return result.embeddings


def embed_query(text: str) -> list[float]:
    """Embed a single query (asymmetric — uses the `query` input type)."""
    result = _client().embed(
        [text],
        model=settings.embed_model,
        input_type="query",
        output_dimension=settings.embed_dim,
    )
    return result.embeddings[0]
