"""FastMCP server exposing the agentic RAG pipeline as MCP tools."""

from __future__ import annotations

import sys
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from . import ingest as ingest_mod
from . import store
from .config import settings
from .graph import build_graph
from .tracing import init_tracing

mcp = FastMCP("Agentic RAG MCP")


@mcp.tool
def ingest(
    url: Annotated[str, Field(description="The web page URL to scrape, chunk, embed, and add "
                                          "to the knowledge base.")],
) -> dict[str, Any]:
    """Add a web page to the knowledge base: scrape the URL, chunk and embed its text, and
    store it so future `ask`/`search` calls can use it. Use this to teach the system new
    source material before querying it."""
    count = ingest_mod.ingest_url(url)
    return {"url": url, "chunks_added": count}


@mcp.tool
def ask(
    question: Annotated[str, Field(description="A natural-language question to answer from the "
                                               "knowledge base.")],
) -> dict[str, Any]:
    """Answer a QUESTION with a written, source-cited answer (the full multi-agent RAG
    pipeline: plan → retrieve → synthesize → self-critique). Use this when the user wants an
    ANSWER. For raw matching documents instead of a written answer, use `search`."""
    result = build_graph().invoke({"question": question})
    return {
        "answer": result.get("answer", ""),
        "citations": result.get("citations", []),
        "plan": result.get("plan", ""),
        "grounded": (result.get("critique") or {}).get("grounded"),
    }


@mcp.tool
def search(
    query: Annotated[str, Field(description="The search query to match against stored "
                                            "document chunks.")],
    k: Annotated[int, Field(description="How many top matching chunks to return.")] = 5,
) -> list[dict[str, Any]]:
    """Retrieve the raw top-k source chunks matching a QUERY, with similarity scores and no
    synthesized answer. Use this when you want the underlying documents themselves. To get a
    written, cited answer instead, use `ask`."""
    return store.search(query, k=k)


def main() -> None:
    # stderr, not stdout — stdout carries the MCP protocol on stdio transport.
    if init_tracing():
        print("observability: Phoenix tracing enabled", file=sys.stderr)
    if settings.transport == "http":
        mcp.run(transport="http", host=settings.http_host, port=settings.http_port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
