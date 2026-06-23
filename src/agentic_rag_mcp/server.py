"""FastMCP server exposing the agentic RAG pipeline as MCP tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from . import ingest as ingest_mod
from . import store
from .config import settings
from .graph import build_graph

mcp = FastMCP("Agentic RAG MCP")


@mcp.tool
def ingest(url: str) -> dict[str, Any]:
    """Scrape a URL, chunk + embed it, and add it to the knowledge base."""
    count = ingest_mod.ingest_url(url)
    return {"url": url, "chunks_added": count}


@mcp.tool
def ask(question: str) -> dict[str, Any]:
    """Answer a question with the multi-agent RAG pipeline; returns answer + citations."""
    result = build_graph().invoke({"question": question})
    return {
        "answer": result.get("answer", ""),
        "citations": result.get("citations", []),
        "plan": result.get("plan", ""),
        "grounded": (result.get("critique") or {}).get("grounded"),
    }


@mcp.tool
def search(query: str, k: int = 5) -> list[dict[str, Any]]:
    """Return the top-k most relevant stored chunks for a query (retrieval only)."""
    return store.search(query, k=k)


def main() -> None:
    if settings.transport == "http":
        mcp.run(transport="http", host=settings.http_host, port=settings.http_port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
