"""Opt-in observability: OpenTelemetry traces to Arize Phoenix.

Enable with `PHOENIX_ENABLED=1` (optionally `PHOENIX_COLLECTOR_ENDPOINT`, default
`http://localhost:6006/v1/traces`). Install the extras first:

    pip install -e ".[trace]"
    phoenix serve          # local Phoenix UI on :6006

Every `ask` run then appears as a full trace: LangGraph node spans (plan → retrieve →
research → synthesize → critique) plus the underlying Claude calls, with token counts
and latencies per span.
"""

from __future__ import annotations

import os


def init_tracing() -> bool:
    """Register Phoenix OTel tracing if PHOENIX_ENABLED is set. Returns True when active."""
    if os.getenv("PHOENIX_ENABLED", "").lower() not in {"1", "true", "yes"}:
        return False
    try:
        from openinference.instrumentation.anthropic import AnthropicInstrumentor
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from phoenix.otel import register
    except ImportError as exc:  # pragma: no cover - depends on optional extras
        raise RuntimeError(
            "PHOENIX_ENABLED is set but tracing dependencies are missing — "
            'install them with: pip install -e ".[trace]"'
        ) from exc

    tracer_provider = register(
        project_name="agentic-rag-mcp",
        endpoint=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
        batch=True,
    )
    # LangGraph nodes run as LangChain runnables -> node-level spans.
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    # Direct Anthropic SDK calls (llm.py) -> LLM spans with token usage.
    AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
    return True
