"""Web research via the Firecrawl v4 Python SDK. Optional — no-ops without an API key.

Uses the v4 `Firecrawl` client: `scrape(url, formats=[...]) -> Document` and
`search(query, limit=...) -> SearchData` (results under `.web`). Reads are attribute-
or key-based so it tolerates both the Pydantic objects and dict-shaped responses.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from .config import settings


@lru_cache(maxsize=1)
def _client() -> Any:
    from firecrawl import Firecrawl

    return Firecrawl(api_key=settings.firecrawl_api_key)


def _field(obj: Any, name: str, default: Any = "") -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def scrape(url: str) -> str:
    """Return clean markdown for a URL (main content only)."""
    doc = _client().scrape(url, formats=["markdown"], only_main_content=True)
    return _field(doc, "markdown", "") or _field(doc, "content", "") or ""


def search_web(query: str, limit: int = 4) -> list[dict[str, Any]]:
    """Search the web and return [{source, content}]; [] if disabled or on error."""
    if not settings.web_enabled:
        return []
    try:
        res = _client().search(query, limit=limit)
    except Exception:
        return []

    results = _field(res, "web", None) or []
    out: list[dict[str, Any]] = []
    for r in results:
        text = _field(r, "markdown", "") or _field(r, "description", "") or ""
        out.append({"source": _field(r, "url", ""), "content": (text or "")[:2000]})
    return out
