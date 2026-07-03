"""AWS Lambda handler: the same grounded-RAG idea, on a pure-AWS stack.

Bedrock does BOTH jobs the Railway deploy gives to Voyage + Anthropic:
  - embeddings  -> Amazon Titan Text Embeddings V2
  - generation  -> Anthropic Claude (on Bedrock)

No external vector DB: the eval corpus is bundled and embedded once at cold start,
then searched in-memory with plain cosine (the corpus is tiny). Exposed over a
Lambda Function URL. This is the "same RAG, two clouds" companion to the main server.
"""

from __future__ import annotations

import json
import math
import os
import pathlib

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
EMBED_MODEL_ID = os.environ.get("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
# Amazon Nova is enabled instantly on any account. Anthropic Claude on Bedrock needs a
# one-time account authorization (a support case on brand-new accounts) — once granted,
# just set LLM_MODEL_ID to a Claude id; the Converse API call below is model-agnostic.
LLM_MODEL_ID = os.environ.get("LLM_MODEL_ID", "us.amazon.nova-lite-v1:0")
EMBED_DIM = int(os.environ.get("EMBED_DIM", "1024"))
TOP_K = int(os.environ.get("TOP_K", "4"))

_bedrock = boto3.client("bedrock-runtime", region_name=REGION)
_INDEX: list[tuple[str, str, list[float]]] = []  # (text, source, vector)

SYNTH_SYSTEM = (
    "You are a careful research assistant. Answer ONLY from the numbered context provided. "
    "Cite every claim with bracketed numbers like [1], [2] that refer to the context items. "
    "If the context is insufficient, say so plainly instead of guessing."
)


def _chunk(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    text = text.strip()
    out, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            nl = text.rfind("\n", start, end)
            if nl > start + size // 2:
                end = nl
        piece = text[start:end].strip()
        if piece:
            out.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return out


def _embed(text: str) -> list[float]:
    resp = _bedrock.invoke_model(
        modelId=EMBED_MODEL_ID,
        body=json.dumps({"inputText": text, "dimensions": EMBED_DIM, "normalize": True}),
    )
    return json.loads(resp["body"].read())["embedding"]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _ensure_index() -> None:
    if _INDEX:
        return
    corpus_dir = pathlib.Path(__file__).parent / "corpus"
    for path in sorted(corpus_dir.glob("*.md")):
        for chunk in _chunk(path.read_text(encoding="utf-8")):
            _INDEX.append((chunk, f"eval-corpus/{path.name}", _embed(chunk)))


def _ask(question: str) -> dict:
    _ensure_index()
    qv = _embed(question)
    ranked = sorted(_INDEX, key=lambda it: _cosine(qv, it[2]), reverse=True)[:TOP_K]
    context = "\n\n".join(
        f"[{i}] (source: {src})\n{txt}" for i, (txt, src, _) in enumerate(ranked, 1)
    )
    prompt = (
        f"Question: {question}\n\nContext:\n{context}\n\n"
        "Write a grounded answer citing sources with [n]."
    )
    # Converse API: one shape for every Bedrock chat model (Nova, Claude, Llama, ...).
    resp = _bedrock.converse(
        modelId=LLM_MODEL_ID,
        system=[{"text": SYNTH_SYSTEM}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 1024, "temperature": 0.2},
    )
    answer = resp["output"]["message"]["content"][0]["text"]
    citations = [{"n": i, "source": src} for i, (_, src, _) in enumerate(ranked, 1)]
    return {"answer": answer, "citations": citations, "backend": "aws-bedrock"}


def handler(event, _context):
    """Lambda Function URL entrypoint. POST {"question": "..."} -> grounded answer."""
    try:
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            import base64
            raw = base64.b64decode(raw).decode("utf-8")
        question = (json.loads(raw).get("question") or "").strip()
        if not question:
            return {"statusCode": 400, "body": json.dumps({"error": "missing 'question'"})}
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(_ask(question)),
        }
    except Exception as exc:  # surface errors as JSON, not a 502
        return {"statusCode": 500, "body": json.dumps({"error": str(exc)})}
