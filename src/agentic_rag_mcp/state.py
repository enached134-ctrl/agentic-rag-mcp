"""Shared LangGraph state for the agentic RAG pipeline."""

from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    question: str
    plan: str
    queries: list[str]
    chunks: list[dict[str, Any]]
    web: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]
    critique: dict[str, Any]
    revisions: int
