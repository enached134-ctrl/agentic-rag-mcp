"""The five LangGraph agent nodes: plan → retrieve → research → synthesize → critique."""

from __future__ import annotations

from typing import Any

from . import llm, store, web
from .config import settings
from .state import GraphState

PLANNER_SYSTEM = (
    "You are a retrieval planner. Given a question, produce a short plan and a list of "
    "focused search queries that, together, would surface the evidence needed to answer it."
)

SYNTH_SYSTEM = (
    "You are a careful research assistant. Answer ONLY from the numbered context provided. "
    "Cite every claim with bracketed numbers like [1], [2] that refer to the context items. "
    "If the context is insufficient, say so plainly instead of guessing."
)

CRITIC_SYSTEM = (
    "You are a strict fact-checker. Decide whether the answer is fully supported by the "
    "numbered context. Penalise unsupported claims and missing citations."
)


def planner_node(state: GraphState) -> dict[str, Any]:
    question = state["question"]
    data = llm.complete_json(
        f"Question: {question}\n\n"
        'Return JSON: {"plan": "<one or two sentences>", '
        '"queries": ["<query 1>", "<query 2>", "<query 3>"]}',
        system=PLANNER_SYSTEM,
        thinking=True,
    )
    plan = data.get("plan", "") if isinstance(data, dict) else ""
    queries = data.get("queries") if isinstance(data, dict) else None
    if not queries:
        queries = [question]
    return {"plan": plan, "queries": queries[:5], "revisions": 0}


def retrieve_node(state: GraphState) -> dict[str, Any]:
    queries = state.get("queries") or [state["question"]]
    seen: set[str] = set()
    chunks: list[dict[str, Any]] = []
    for q in queries:
        for hit in store.search(q, k=settings.top_k):
            if hit["id"] not in seen:
                seen.add(hit["id"])
                chunks.append(hit)
    chunks.sort(key=lambda c: c.get("score", 0.0), reverse=True)
    return {"chunks": chunks[: settings.top_k * 2]}


def research_node(state: GraphState) -> dict[str, Any]:
    if not settings.web_enabled:
        return {"web": []}
    return {"web": web.search_web(state["question"], limit=4)}


def _context_items(state: GraphState) -> list[dict[str, Any]]:
    return list(state.get("chunks") or []) + list(state.get("web") or [])


def _render_context(items: list[dict[str, Any]]) -> str:
    lines = []
    for i, it in enumerate(items, start=1):
        src = it.get("source") or "unknown"
        lines.append(f"[{i}] (source: {src})\n{it.get('content', '')}")
    return "\n\n".join(lines) if lines else "(no context retrieved)"


def synthesize_node(state: GraphState) -> dict[str, Any]:
    items = _context_items(state)
    context = _render_context(items)
    feedback = ""
    crit = state.get("critique")
    if crit and not crit.get("grounded", True):
        feedback = f"\n\nA reviewer flagged the previous draft: {crit.get('feedback', '')}\nFix it."

    answer = llm.complete(
        f"Question: {state['question']}\n\nContext:\n{context}{feedback}\n\n"
        "Write a complete, well-structured answer grounded only in the context, "
        "citing sources with [n].",
        system=SYNTH_SYSTEM,
        thinking=True,
        max_tokens=2048,
    )
    citations = [
        {"n": i, "source": it.get("source", ""), "score": it.get("score")}
        for i, it in enumerate(items, start=1)
    ]
    return {"answer": answer, "citations": citations}


def critique_node(state: GraphState) -> dict[str, Any]:
    context = _render_context(_context_items(state))
    verdict = llm.complete_json(
        f"Question: {state['question']}\n\nContext:\n{context}\n\n"
        f"Answer to check:\n{state.get('answer', '')}\n\n"
        'Return JSON: {"grounded": <true|false>, "feedback": "<what is unsupported or missing>"}',
        system=CRITIC_SYSTEM,
        thinking=True,
    )
    grounded = bool(verdict.get("grounded", True)) if isinstance(verdict, dict) else True
    feedback = verdict.get("feedback", "") if isinstance(verdict, dict) else ""
    return {
        "critique": {"grounded": grounded, "feedback": feedback},
        "revisions": state.get("revisions", 0) + 1,
    }


def route_after_critique(state: GraphState) -> str:
    crit = state.get("critique") or {}
    if crit.get("grounded", True):
        return "done"
    if state.get("revisions", 0) <= settings.max_revisions:
        return "revise"
    return "done"
