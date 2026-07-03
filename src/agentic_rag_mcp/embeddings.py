"""Embeddings via Voyage AI (Anthropic's recommended embeddings partner)."""

from __future__ import annotations

from functools import lru_cache

import voyageai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import settings


@lru_cache(maxsize=1)
def _client() -> voyageai.Client:
    return voyageai.Client(api_key=settings.voyage_api_key)


# Voyage's free tier caps at 3 requests/minute until a payment method is on file.
# Wait past the full 60s rate window (not just a few seconds) and retry enough times
# that a single request always clears once the window resets.
@retry(
    retry=retry_if_exception_type(voyageai.error.RateLimitError),
    wait=wait_exponential(multiplier=2, min=15, max=75),
    stop=stop_after_attempt(8),
    reraise=True,
)
def _embed(texts: list[str], input_type: str) -> list[list[float]]:
    return _client().embed(
        texts,
        model=settings.embed_model,
        input_type=input_type,
        output_dimension=settings.embed_dim,
    ).embeddings


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of documents for storage (one request for the whole batch)."""
    if not texts:
        return []
    return _embed(texts, "document")


def embed_query(text: str) -> list[float]:
    """Embed a single query (asymmetric — uses the `query` input type)."""
    return _embed([text], "query")[0]
