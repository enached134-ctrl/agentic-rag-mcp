"""Smoke tests that need no network, database, or API keys."""

from __future__ import annotations

from agentic_rag_mcp import ingest
from agentic_rag_mcp.config import settings
from agentic_rag_mcp.llm import _loads_lenient


def test_chunk_text_splits_with_overlap():
    text = ("para one.\n" * 200).strip()
    chunks = ingest.chunk_text(text, size=200, overlap=40)
    assert len(chunks) > 1
    assert all(chunks)
    assert all(len(c) <= 240 for c in chunks)  # size + a little slack


def test_chunk_text_empty():
    assert ingest.chunk_text("") == []
    assert ingest.chunk_text("   ") == []


def test_loads_lenient_handles_fenced_json():
    assert _loads_lenient('```json\n{"a": 1}\n```') == {"a": 1}
    assert _loads_lenient('here you go: {"grounded": true}') == {"grounded": True}
    assert _loads_lenient("not json at all") == {}


def test_defaults():
    assert settings.model  # has a default model id
    assert settings.embed_dim == 1024


def test_graph_compiles():
    from agentic_rag_mcp.graph import build_graph

    graph = build_graph()
    assert hasattr(graph, "invoke")
