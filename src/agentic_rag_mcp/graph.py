"""Assemble the agent nodes into a compiled LangGraph."""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from . import nodes
from .state import GraphState


@lru_cache(maxsize=1)
def build_graph():
    """Build and compile the plan → retrieve → research → synthesize → critique graph."""
    g = StateGraph(GraphState)
    g.add_node("plan", nodes.planner_node)
    g.add_node("retrieve", nodes.retrieve_node)
    g.add_node("research", nodes.research_node)
    g.add_node("synthesize", nodes.synthesize_node)
    g.add_node("critique", nodes.critique_node)

    g.add_edge(START, "plan")
    g.add_edge("plan", "retrieve")
    g.add_edge("retrieve", "research")
    g.add_edge("research", "synthesize")
    g.add_edge("synthesize", "critique")
    g.add_conditional_edges(
        "critique",
        nodes.route_after_critique,
        {"revise": "synthesize", "done": END},
    )
    return g.compile()
