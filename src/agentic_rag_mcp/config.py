"""Central configuration, loaded from environment / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # load a local .env if present; real env vars take precedence


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    # LLM (Anthropic)
    anthropic_api_key: str
    model: str

    # Embeddings (Voyage AI)
    voyage_api_key: str
    embed_model: str
    embed_dim: int

    # Vector store (Postgres + pgvector, e.g. Supabase)
    database_url: str

    # Web research (Firecrawl) — optional
    firecrawl_api_key: str

    # Graph behaviour
    top_k: int
    max_revisions: int

    # MCP transport
    transport: str
    http_host: str
    http_port: int

    @property
    def web_enabled(self) -> bool:
        return bool(self.firecrawl_api_key)


def load_settings() -> Settings:
    return Settings(
        anthropic_api_key=_env("ANTHROPIC_API_KEY"),
        model=_env("RAG_MODEL", "claude-opus-4-8"),
        voyage_api_key=_env("VOYAGE_API_KEY"),
        embed_model=_env("RAG_EMBED_MODEL", "voyage-3.5"),
        embed_dim=int(_env("RAG_EMBED_DIM", "1024")),
        database_url=_env("DATABASE_URL"),
        firecrawl_api_key=_env("FIRECRAWL_API_KEY"),
        top_k=int(_env("RAG_TOP_K", "5")),
        max_revisions=int(_env("RAG_MAX_REVISIONS", "1")),
        transport=_env("RAG_TRANSPORT", "stdio"),
        http_host=_env("RAG_HTTP_HOST", "0.0.0.0"),
        # Fall back to the platform-injected $PORT (Railway/Fly/Cloud Run) when set.
        http_port=int(_env("RAG_HTTP_PORT") or _env("PORT", "8000")),
    )


settings = load_settings()
