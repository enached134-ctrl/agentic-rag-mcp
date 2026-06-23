"""Thin Anthropic (Claude) helper used by the agent nodes."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import anthropic

from .config import settings


@lru_cache(maxsize=1)
def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def complete(
    prompt: str,
    *,
    system: str | None = None,
    max_tokens: int = 2048,
    thinking: bool = False,
) -> str:
    """Single-turn completion. Returns the concatenated text blocks.

    `thinking=True` enables adaptive thinking (recommended on Claude 4.x for
    multi-step reasoning); thinking blocks are produced and billed but only the
    final text is returned here.
    """
    kwargs: dict[str, Any] = {
        "model": settings.model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    if thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    msg = _client().messages.create(**kwargs)
    return "".join(block.text for block in msg.content if block.type == "text").strip()


def complete_json(
    prompt: str,
    *,
    system: str | None = None,
    max_tokens: int = 2048,
    thinking: bool = False,
) -> Any:
    """Like `complete`, but parses the model's reply as JSON.

    Tolerates ```json fences and surrounding prose by extracting the first
    balanced JSON object/array. Returns {} on unrecoverable output.
    """
    text = complete(
        prompt + "\n\nRespond with ONLY valid JSON. No prose, no code fences.",
        system=system,
        max_tokens=max_tokens,
        thinking=thinking,
    )
    return _loads_lenient(text)


def _loads_lenient(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        # strip a leading ```json / ``` fence and the trailing ```
        text = text.split("```", 2)[1] if text.count("```") >= 2 else text.strip("`")
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to the first balanced {...} or [...] span.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    return {}
