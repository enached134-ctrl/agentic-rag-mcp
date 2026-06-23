"""promptfoo Python provider — routes each test prompt through the RAG `ask` pipeline.

Requires the package installed and env configured (ANTHROPIC_API_KEY, VOYAGE_API_KEY,
DATABASE_URL) plus an ingested knowledge base.
"""

from __future__ import annotations

from typing import Any


def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    from agentic_rag_mcp.graph import build_graph

    result = build_graph().invoke({"question": prompt})
    return {
        "output": result.get("answer", ""),
        "metadata": {
            "grounded": (result.get("critique") or {}).get("grounded"),
            "num_citations": len(result.get("citations", [])),
        },
    }
